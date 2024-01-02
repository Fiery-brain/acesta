from django.db import models

from acesta.geo.models import City
from acesta.geo.models import Region
from acesta.stats.models.abstract import Audience


class AudienceRegions(Audience):
    """
    Regions audience
    """

    code = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.CASCADE,
        related_name="region_audience",
    )

    class Meta:
        unique_together = [
            "code",
            "sex",
            "age",
            "tourism_type",
        ]
        indexes = [
            models.Index(fields=["code", "v_type_sex_age"]),
            models.Index(fields=["code", "v_type_sex_age", "tourism_type"]),
        ]
        verbose_name = "Аудитория в регинах"
        verbose_name_plural = "Аудитория в регинах"


class AudienceCities(Audience):
    """
    Cities audience
    """

    code = models.ForeignKey(
        City,
        verbose_name="Город",
        on_delete=models.CASCADE,
        related_name="city_audience",
    )

    class Meta:
        unique_together = [
            "code",
            "sex",
            "age",
            "tourism_type",
        ]
        indexes = [
            models.Index(fields=["code", "v_type_sex_age"]),
            models.Index(fields=["code", "v_type_sex_age", "tourism_type"]),
        ]
        verbose_name = "Аудитория в городах"
        verbose_name_plural = "Аудитория в городах"
