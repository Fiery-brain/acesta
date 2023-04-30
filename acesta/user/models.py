from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from model_utils.models import TimeStampedModel

from acesta.geo.models import City
from acesta.geo.models import Region
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

    period_dateformat = "%d.%m.%Y %H:%M:%S %z"

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
        "Фамилия", max_length=150, validators=[validate_russian]
    )
    middle_name = models.CharField(
        "Отчество", max_length=50, validators=[validate_russian]
    )
    phone = models.CharField(
        "Телефон",
        max_length=12,
        blank=True,
        null=True,
    )
    company = models.CharField(
        "Компания",
        max_length=100,
        blank=True,
        null=True,
    )
    position = models.CharField(
        "Должность",
        max_length=80,
        blank=True,
        null=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "middle_name",
        "region",
    ]

    def save(self, *args, **kwargs):
        if self.pk is None:
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

    def update_period_info(self, period, order_regions):
        period_info = self.period_info
        for region in order_regions.all():
            region_period_data = {region.code: {}}
            if region.code in period_info.keys():
                end = datetime.strptime(
                    period_info.get(region.code).get("end"), self.period_dateformat
                )
                end += relativedelta(months=period)
                region_period_data[region.code]["start"] = period_info.get(
                    region.code
                ).get("start")
                region_period_data[region.code]["end"] = datetime.strftime(
                    end, self.period_dateformat
                )
            else:
                start = timezone.now()
                end = start + relativedelta(months=period)
                region_period_data[region.code]["start"] = datetime.strftime(
                    start, self.period_dateformat
                )
                region_period_data[region.code]["end"] = datetime.strftime(
                    end, self.period_dateformat
                )
            self.regions.add(region)
            self.period_info.update(region_period_data)
            self.save()

    def clean_up_old_periods(self):
        old_periods = []
        for region, period in self.period_info.items():
            end_date = datetime.strptime(period.get("end"), self.period_dateformat)
            if end_date < now():
                old_region = Region.objects.get(code=region)
                self.regions.remove(old_region)
                old_periods.append(region)
        for region in old_periods:
            del self.period_info[region]
        if len(old_periods):
            self.save()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]


class Order(TimeStampedModel):
    """
    Order Model
    """

    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.DO_NOTHING,
        related_name="user_orders",
    )
    period = models.IntegerField("Период (месяцев)")
    cost = models.DecimalField(
        "Стоимость", decimal_places=2, max_digits=10, default=0.0
    )
    discount = models.DecimalField(
        "Скидка", decimal_places=2, max_digits=10, default=0.0
    )
    total = models.DecimalField("Итого", decimal_places=2, max_digits=10, default=0.0)
    regions = models.ManyToManyField(
        Region,
        verbose_name="Регионы",
        related_name="region_orders",
        blank=True,
    )
    begin_time = models.DateTimeField(
        "Дата начала",
        blank=True,
        null=True,
    )
    end_time = models.DateTimeField(
        "Дата конца",
        blank=True,
        null=True,
    )
    state = models.CharField(
        "Статус",
        max_length=10,
        choices=(
            (settings.STATE_NEW, "в обработке"),
            (settings.STATE_WAITING, "ожидает оплаты"),
            (settings.STATE_PAID, "оплачена"),
            (settings.STATE_CANCELED, "отменена"),
            (settings.STATE_DONE, "выполнена"),
        ),
        default="new",
    )

    @staticmethod
    def get_cost(period: int, regions_list: list):
        """
        Returns access cost by period and regions list
        :param period: int
        :param regions_list: list
        :return: int
        """
        regions = Region.objects.filter(code__in=regions_list)
        cost = 0
        for region in regions:
            cost += period * settings.PRICES.get(f"rank_{region.rank}", 0)
        return cost

    @staticmethod
    def get_discount(period: int):
        """
        Returns discount by period
        :param period: int
        :return: float
        """
        discount = 0
        if 6 <= period < 12:
            discount = settings.PRICES.get("gt_6_discount", 0)
        elif period >= 12:
            discount = settings.PRICES.get("gt_12_discount", 0)
        return discount

    @staticmethod
    def get_discount_sum(period: int, regions_list: list):
        """
        Returns discount sum by period
        :param period: int
        :param regions_list: list
        :return: float
        """
        return Order.get_discount(period) / 100 * Order.get_cost(period, regions_list)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            order = Order.objects.get(pk=self.pk)
            if self.state == settings.STATE_DONE and order.state != settings.STATE_DONE:
                self.user.update_period_info(self.period, self.regions)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-modified"]


class Support(TimeStampedModel):
    """
    Support Model
    """

    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.DO_NOTHING,
        related_name="user_messages",
    )
    subject = models.CharField("Тема", max_length=10, choices=settings.SUPPORT_SUBJECTS)
    message = models.TextField(
        "Сообщение",
    )
    state = models.CharField(
        "Статус",
        max_length=10,
        choices=(
            (settings.STATE_NEW, "в обработке"),
            (settings.STATE_DONE, "обработана"),
        ),
        default="new",
    )

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"
        ordering = ["-modified"]


def recalc_sums_after_change_period(sender, instance, *args, **kwargs) -> None:
    """
    Recalculates Order sums
    :param sender: Order
    :param instance: Order
    :return: None
    """
    if instance.pk:
        regions_list = [region.code for region in instance.regions.all()]
        instance.cost = Order.get_cost(instance.period, regions_list)
        instance.discount = Order.get_discount_sum(instance.period, regions_list)
        instance.total = instance.cost - instance.discount


def recalc_sums_after_change_regions(sender, **kwargs) -> None:
    """
    Recalculates Order sums
    :param sender: Order.regions.through
    :param kwargs: dict
    :return: None
    """
    instance = kwargs.pop("instance")
    pk_set = kwargs.pop("pk_set")
    instance.cost = Order.get_cost(instance.period, pk_set)
    instance.discount = Order.get_discount_sum(instance.period, pk_set)
    instance.total = instance.cost - instance.discount
    instance.save(update_fields=["cost", "discount", "total"])


models.signals.pre_save.connect(recalc_sums_after_change_period, sender=Order)
models.signals.m2m_changed.connect(
    recalc_sums_after_change_regions, sender=Order.regions.through
)
