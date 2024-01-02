from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.timezone import now

from acesta.geo.models import City
from acesta.geo.models import Region
from acesta.geo.models import SightGroup
from acesta.user import format_date
from acesta.user import get_date
from acesta.user.validators import validate_russian


class UserManager(BaseUserManager):
    """
    User Model with prefetch related fields
    """

    def get(self, *args, **kwargs):
        return (
            super()
            .prefetch_related("current_region", "region", "regions")
            .get(*args, **kwargs)
        )


class User(AbstractUser):
    """
    User Model
    """

    email = models.EmailField("Email", unique=True)
    regions = models.ManyToManyField(
        Region,
        verbose_name="Оплаченные регионы",
        related_name="paid_regions_users",
        blank=True,
    )
    period_info = models.JSONField(
        "Периоды полного доступа",
        default=dict,
        blank=True,
        null=True,
    )
    tourism_types = ArrayField(
        models.CharField(
            "Оплаченные виды туризма",
            max_length=10,
            choices=settings.TOURISM_TYPES,
        ),
        blank=True,
        null=True,
    )
    current_region = models.ForeignKey(
        Region,
        verbose_name="Последний регион",
        on_delete=models.DO_NOTHING,
        related_name="current_region_users",
    )
    region = models.ForeignKey(
        Region,
        verbose_name="Домашний регион",
        on_delete=models.DO_NOTHING,
        related_name="home_region_users",
        default="01",
    )
    city = models.ForeignKey(
        City,
        verbose_name="Город",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
    )
    first_name = models.CharField("Имя", max_length=150, validators=[validate_russian])
    last_name = models.CharField(
        "Фамилия",
        max_length=150,
        validators=[validate_russian],
        blank=True,
        null=True,
    )
    middle_name = models.CharField(
        "Отчество",
        max_length=50,
        validators=[validate_russian],
        blank=True,
        null=True,
    )
    phone = models.CharField(
        "Телефон",
        max_length=12,
        blank=True,
        null=True,
    )
    company = models.CharField(
        "Компания",
        max_length=130,
        blank=True,
        null=True,
    )
    position = models.CharField(
        "Должность",
        max_length=130,
        blank=True,
        null=True,
    )
    points = models.SmallIntegerField("Контакты", default=0)
    purpose = models.CharField("Цель", max_length=1200, blank=True, null=True)
    note = models.CharField("Заметки", max_length=255, blank=True, null=True)
    subscription = models.BooleanField("Подписка на новости", default=True)
    registered = models.BooleanField("Регистрация завершена", default=False)
    last_hit = models.DateTimeField(
        "Последний хит",
        blank=True,
        null=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "region",
    ]

    def save(self, *args, **kwargs):
        if self.pk is None:
            if not hasattr(self, "region"):
                self.region = Region.objects.get(
                    pk=User._meta.get_field("region").get_default()
                )
            self.current_region = self.region
        self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{ self.email } { self.last_name } { self.first_name }"
            f" { self.middle_name }{ ' (' + getattr(self.city, 'title') + ')' if self.city else ''}"
        )

    @property
    def is_extended(self) -> bool:
        """
        Returns True if user has full access to current region
        :return: bool
        """
        return (
            self.current_region.rank == 0 or self.current_region in self.regions.all()
        )

    @property
    def is_accustomed(self) -> bool:
        """
        Returns True if user is already experienced
        :return: bool
        """
        return self.date_joined + relativedelta(days=14) < now()

    def update_period_info(self, period, order_regions, tourism_types):
        period_info = self.period_info

        for region in order_regions.all():
            region_period_data = {region.code: {}}

            if period == 0.25:
                delta_args = dict(days=7)
            elif period == 0.5:
                delta_args = dict(days=14)
            else:
                delta_args = dict(months=period)
            if region.code in period_info.keys():
                region_period_data[region.code] = period_info.get(region.code)
                if (
                    get_date(format_date(now()))
                    - get_date(period_info.get(region.code).get("start"))
                ).seconds // 60:
                    end = get_date(period_info.get(region.code).get("end"))
                    end += relativedelta(**delta_args)
                    region_period_data[region.code]["start"] = period_info.get(
                        region.code
                    ).get("start")
                    region_period_data[region.code]["end"] = format_date(end)
            else:
                start = now()
                end = start + relativedelta(**delta_args)
                region_period_data[region.code]["start"] = format_date(start)
                region_period_data[region.code]["end"] = format_date(end)
            self.regions.add(region)
            self.period_info.update(region_period_data)
        if self.tourism_types is None:
            self.tourism_types = tourism_types
        else:
            self.tourism_types = list(set(self.tourism_types + tourism_types))
        self.save()

    def clean_up_old_periods(self):
        old_periods = []
        for region, period in self.period_info.items():
            end_date = get_date(period.get("end"))
            if end_date < now():
                old_region = Region.objects.get(code=region)
                self.regions.remove(old_region)
                old_periods.append(region)
        for region in old_periods:
            del self.period_info[region]
        if len(old_periods):
            if not len(self.period_info):
                self.tourism_types = None
            self.save(update_fields=["period_info", "tourism_types"])

    @property
    def is_set_tourism_types(self) -> bool:
        """
        Returns True if user has filtered tourism types
        :return: bool
        """
        return self.tourism_types is not None and len(self.tourism_types)

    def get_current_tourism_type(self, tourism_type=None) -> str or None:
        """
        Checks if tourism type is open for user
        and return the first permitted
        :param tourism_type: str
        :return: str
        """
        if self.is_set_tourism_types:
            if tourism_type is None or tourism_type not in self.tourism_types:
                tourism_type = sorted(self.tourism_types)[0]
        return tourism_type

    def get_current_sight_group(self, sight_group) -> str or None:
        """
        Checks if sight group is open for user
        and return the first permitted
        :param sight_group: str
        :return: str
        """
        if self.tourism_types is not None and len(self.tourism_types):
            sight_groups = SightGroup.objects.filter(
                tourism_type__in=self.tourism_types
            )
            if sight_group is None or not len(sight_groups.filter(name=sight_group)):
                sight_group = sight_groups.first().name
        return sight_group

    def set_last_hit(self):
        self.last_hit = now()
        self.save(update_fields=["last_hit"])

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]
