from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ProcessStageNotReady(RuntimeError):
    def __init__(self, cycle, stage, missing_stages):
        self.cycle = cycle
        self.stage = stage
        self.missing_stages = tuple(missing_stages)
        super().__init__(
            f"{cycle}:{stage} requires completed stages: "
            f"{', '.join(self.missing_stages)}"
        )


class _ProcessRegistryClose:
    def __get__(self, marker, owner):
        if marker is not None:
            return marker.delete

        def close(domain, process, *parts):
            return owner.objects.filter(
                key=owner.make_key(domain, process, *parts),
            ).delete()

        return close


class ProcessRegistry(models.Model):
    """
    Registry of unfinished service processes.
    """

    domain = models.CharField(max_length=50, db_index=True)
    process = models.CharField(max_length=100, db_index=True)
    key = models.CharField(max_length=255, unique=True, db_index=True)
    data = models.JSONField(default=dict, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    @classmethod
    def make_key(cls, domain, process, *parts):
        return ":".join(str(part) for part in (domain, process, *parts))

    @classmethod
    def open(cls, domain, process, *parts, data=None):
        marker, created = cls.objects.get_or_create(
            key=cls.make_key(domain, process, *parts),
            defaults={
                "domain": domain,
                "process": process,
                "data": data or {},
            },
        )
        if data is not None and not created:
            marker.data = data
            marker.save(update_fields=["data", "modified"])
        return marker

    @classmethod
    def get_open(cls, domain, process, *parts):
        try:
            return cls.objects.get(key=cls.make_key(domain, process, *parts))
        except cls.DoesNotExist:
            return None

    @classmethod
    def has_open(cls, domain, process, *parts):
        return cls.objects.filter(key=cls.make_key(domain, process, *parts)).exists()

    @classmethod
    def cleanup(cls, days=31, domain=None, process=None):
        qs = cls.objects.filter(modified__lt=timezone.now() - timedelta(days=days))
        if domain is not None:
            qs = qs.filter(domain=domain)
        if process is not None:
            qs = qs.filter(process=process)
        return qs.delete()

    def update_data(self, **values):
        self.data = {
            **(self.data or {}),
            **values,
        }
        self.save(update_fields=["data", "modified"])
        return self

    def get_data(self, name, default=None):
        return (self.data or {}).get(name, default)

    close = _ProcessRegistryClose()

    def __str__(self):
        return self.key

    class Meta:
        verbose_name = "Реестр процесса"
        verbose_name_plural = "Реестр процессов"
        ordering = ("domain", "process", "key")


class ProcessCycle:
    """
    Lightweight process stage controller backed by ProcessRegistry.
    """

    @classmethod
    def _get_cycle_config(cls, cycle):
        try:
            return settings.PROCESS_CYCLES[cycle]
        except KeyError as error:
            raise KeyError(f"Unknown process cycle: {cycle}") from error

    @classmethod
    def get_required_stages(cls, cycle, stage):
        stages = cls._get_cycle_config(cycle)["stages"]
        if stage not in stages:
            raise KeyError(f"Unknown process stage: {cycle}:{stage}")
        return tuple(stages[stage].get("requires", ()))

    @classmethod
    def get_dependent_stages(cls, cycle, required_stage):
        stages = cls._get_cycle_config(cycle)["stages"]
        return tuple(
            stage
            for stage, config in stages.items()
            if required_stage in config.get("requires", ())
        )

    def __init__(self, cycle, *parts):
        self.cycle = cycle
        self.config = self._get_cycle_config(cycle)
        self.stages = self.config["stages"]
        self.marker = ProcessRegistry.open(cycle, "region_cycle", *parts)

    def _check_stage(self, stage):
        if stage not in self.stages:
            raise KeyError(f"Unknown process stage: {self.cycle}:{stage}")

    def _missing_required_stages(self, stage):
        required_stages = self.stages[stage].get("requires", ())
        completed_stages = set(self.marker.get_data("completed_stages", []))
        return [
            required_stage
            for required_stage in required_stages
            if required_stage not in completed_stages
        ]

    def get_missing_required_stages(self, stage):
        self._check_stage(stage)
        return self._missing_required_stages(stage)

    def start_stage(self, stage, force=False):
        self._check_stage(stage)
        missing_stages = self._missing_required_stages(stage)
        if missing_stages and not force:
            raise ProcessStageNotReady(self.cycle, stage, missing_stages)

        data = {"current_stage": stage}
        if missing_stages and force:
            forced_stages = list(self.marker.get_data("forced_stages", []))
            if stage not in forced_stages:
                forced_stages.append(stage)
            data["forced_stages"] = forced_stages
        self.marker.update_data(**data)
        return self

    def complete_stage(self, stage):
        self._check_stage(stage)
        completed_stages = list(self.marker.get_data("completed_stages", []))
        if stage not in completed_stages:
            completed_stages.append(stage)
        self.marker.update_data(
            current_stage=None,
            completed_stages=completed_stages,
        )
        return self

    def has_completed(self, *stages):
        completed_stages = set(self.marker.get_data("completed_stages", []))
        return all(stage in completed_stages for stage in stages)

    def is_ready_for(self, stage):
        self._check_stage(stage)
        return not self._missing_required_stages(stage)

    def close(self):
        return self.marker.close()
