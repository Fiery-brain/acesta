from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from model_utils.models import TimeStampedModel

from acesta.geo.models import Region
from acesta.user.models.user import User


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
