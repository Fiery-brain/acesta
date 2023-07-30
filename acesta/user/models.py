from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.timezone import now
from model_utils.models import TimeStampedModel

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

    def get_current_tourism_type(self, tourism_type=None) -> str or None:
        """
        Checks if tourism type is open for user
        and return the first permitted
        :param tourism_type: str
        :return: str
        """
        if self.tourism_types is not None:
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
        if self.tourism_types is not None:
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
    period = models.FloatField("Период", choices=settings.ORDER_PERIODS)
    tourism_types = ArrayField(
        models.CharField(
            "Виды туризма",
            max_length=10,
            choices=settings.TOURISM_TYPES,
        ),
        blank=True,
        null=True,
    )
    cost = models.DecimalField(
        "Стоимость", decimal_places=2, max_digits=10, default=0.0
    )
    discount = models.DecimalField(
        "Скидка", decimal_places=2, max_digits=10, default=0.0
    )
    inn = models.CharField(
        "ИНН",
        max_length=12,
        blank=True,
        null=True,
    )
    promo = models.CharField(
        "Промокод",
        max_length=10,
        blank=True,
        null=True,
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
    def get_cost(period: float, regions_list: list, tourism_types: list = None):
        """
        Returns access cost by period and regions list
        :param period: float
        :param regions_list: list
        :param tourism_types: list
        :return: int
        """

        def get_period_coef(period):
            coef = period
            if 0 < period <= 0.25:
                coef = settings.PERIOD_1_WEEK_COEF
            elif 0.25 < period <= 0.5:
                coef = settings.PERIOD_2_WEEKS_COEF
            return coef

        regions = Region.objects.filter(code__in=regions_list)
        cost = 0

        for region in regions:
            cost += get_period_coef(period) * settings.PRICES.get(
                f"rank_{region.rank}", 0
            )

        if tourism_types is not None and len(tourism_types):
            cost *= settings.TOURISM_TYPE_COEF * len(tourism_types)
        return int(cost)

    @staticmethod
    def get_discount(period: float):
        """
        Returns discount by period
        :param period: float
        :return: float
        """
        discount = 0
        if 6 <= period < 12:
            discount = settings.PRICES.get("gt_6_discount", 0)
        elif period >= 12:
            discount = settings.PRICES.get("gt_12_discount", 0)
        return discount

    @staticmethod
    def get_discount_sum(period: float, regions_list: list, tourism_types: list = None):
        """
        Returns discount sum by period
        :param period: int
        :param regions_list: list
        :param tourism_types: list
        :return: float
        """
        return (
            Order.get_discount(period)
            / 100
            * Order.get_cost(period, regions_list, tourism_types)
        )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
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
        default=settings.STATE_NEW,
    )

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"
        ordering = ["-modified"]


class Request(TimeStampedModel):
    """
    Request Model
    """

    name = models.CharField("Имя", max_length=35, validators=[validate_russian])
    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.DO_NOTHING,
        related_name="user_requests",
        blank=True,
        null=True,
    )
    channel = models.CharField(
        "Канал связи", max_length=10, choices=settings.REQUEST_CHANNELS
    )
    _id = models.CharField("Номер или ник", max_length=32)
    subject = models.CharField(
        "Тема",
        max_length=15,
        choices=settings.REQUEST_SUBJECTS,
        default=settings.REQUEST_CONSULTATION,
    )
    time = models.DateTimeField("Срок", blank=True, null=True)
    comment = models.CharField("Комментарий", max_length=255, blank=True, null=True)
    note = models.CharField("Заметки", max_length=255, blank=True, null=True)
    region = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.DO_NOTHING,
        related_name="region_requests",
        blank=True,
        null=True,
    )
    interest = models.BooleanField("Интерес", default=True)
    state = models.CharField(
        "Статус",
        max_length=10,
        choices=(
            (settings.STATE_NEW, "новый"),
            (settings.STATE_WAITING, "в ожидании"),
            (settings.STATE_DONE, "обработан"),
        ),
        default=settings.STATE_NEW,
    )

    class Meta:
        verbose_name = "Запросы"
        verbose_name_plural = "Запросы"
        ordering = ["-modified"]


def recalc_sums_after_changes(sender, instance, *args, **kwargs) -> None:
    """
    Recalculates Order sums
    :param sender: Order
    :param instance: Order
    :return: None
    """
    if instance.pk:
        regions_list = [region.code for region in instance.regions.all()]
        instance.cost = Order.get_cost(
            instance.period, regions_list, instance.tourism_types
        )
        instance.discount = Order.get_discount_sum(
            instance.period, regions_list, instance.tourism_types
        )
        instance.total = instance.cost - instance.discount

        order = Order.objects.get(pk=instance.pk)
        if instance.state == settings.STATE_DONE and order.state != settings.STATE_DONE:
            instance.user.update_period_info(
                instance.period, instance.regions, instance.tourism_types
            )


def recalc_sums_after_change_regions(sender, **kwargs) -> None:
    """
    Recalculates Order sums
    :param sender: Order.regions.through
    :param kwargs: dict
    :return: None
    """
    instance = kwargs.pop("instance")
    pk_set = kwargs.pop("pk_set")
    instance.cost = Order.get_cost(instance.period, pk_set, instance.tourism_types)
    instance.discount = Order.get_discount_sum(
        instance.period, pk_set, instance.tourism_types
    )
    instance.total = instance.cost - instance.discount
    if (
        instance.state == settings.STATE_DONE
        and not (instance.modified - instance.created).microseconds
    ):
        instance.user.update_period_info(
            instance.period,
            Region.objects.filter(pk__in=pk_set),
            instance.tourism_types,
        )


models.signals.pre_save.connect(recalc_sums_after_changes, sender=Order)
models.signals.m2m_changed.connect(
    recalc_sums_after_change_regions, sender=Order.regions.through
)
