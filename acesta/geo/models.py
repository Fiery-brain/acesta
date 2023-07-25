from django.conf import settings
from django.db import models
from django.utils import timezone
from model_utils.models import TimeStampedModel


class PubManager(models.Manager):
    """
    Менеджер для выбора только опубликованных записей
    """

    def get_queryset(self):
        return super().get_queryset().filter(is_pub=True)


class Region(TimeStampedModel):
    """
    Регионы
    """

    code = models.CharField(
        "Код региона",
        max_length=2,
        primary_key=True,
    )
    _id = models.IntegerField(
        "Внешний ID",
        unique=True,
    )
    region = models.CharField(
        "Название региона в Яндекс",
        max_length=60,
    )
    title = models.CharField("Название региона", max_length=60, db_index=True)
    region_type = models.CharField(
        "Вид субъекта",
        max_length=30,
        choices=settings.REGION_TYPES,
    )
    rank = models.IntegerField("Ранг", default=0)
    territory = models.IntegerField("Территория", default=0)
    population = models.IntegerField("Численность", default=0)
    zoom_regions = models.FloatField("Zoom", default=3.5)
    zoom_cities = models.FloatField("Zoom", default=5)
    center_lat = models.FloatField("Center latitude", default=69)
    center_lon = models.FloatField("Center longitude", default=105)
    synonyms = models.TextField(
        verbose_name="Синонимы",
        help_text="Введите фразы отделив их переводом строки",
        blank=True,
        null=True,
    )
    is_pub = models.BooleanField(
        "Публиковать",
        default=False,
        db_index=True,
    )
    objects = models.Manager()
    pub = PubManager()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"
        ordering = ("code",)


class City(TimeStampedModel):
    """
    Город
    """

    code = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.CASCADE,
        related_name="region_cities",
    )
    _id = models.IntegerField(
        "Внешний ID",
        unique=True,
    )
    title = models.CharField("Название", max_length=150, db_index=True)
    area = models.CharField(
        "Район",
        max_length=150,
        blank=True,
        null=True,
    )
    lat = models.FloatField(
        verbose_name="Широта",
        default=0.0,
    )
    lon = models.FloatField(
        verbose_name="Долгота",
        default=0.0,
    )
    population = models.IntegerField("Численность", default=0)
    foundation = models.CharField(
        "Год основания",
        max_length=60,
    )
    is_capital = models.BooleanField(
        "Столица",
        default=False,
    )
    is_pub = models.BooleanField(
        "Публиковать",
        default=False,
        db_index=True,
    )
    synonyms = models.TextField(
        verbose_name="Синонимы",
        help_text="Введите фразы отделив их переводом строки",
        blank=True,
        null=True,
    )
    objects = PubManager()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"
        ordering = ("title",)


class SightGroup(TimeStampedModel):
    """
    Группа точки притяжения
    """

    tourism_type = models.CharField(
        "Вид туризма",
        max_length=10,
        choices=settings.TOURISM_TYPES,
        default=settings.TOURISM_TYPE_DEFAULT,
    )
    name = models.CharField(
        "Имя",
        max_length=15,
        primary_key=True,
    )
    title = models.CharField(
        "Название",
        max_length=150,
    )
    title_gen = models.CharField(
        "Название в родительном падеже",
        max_length=150,
    )
    is_pub = models.BooleanField(
        "Публиковать",
        default=False,
        db_index=True,
    )
    objects = models.Manager()
    pub = PubManager()

    def __str__(self):
        return f"{ self.name } { self.title }"

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
        ordering = ("title",)


class Sight(TimeStampedModel):
    """
    Точка притяжения
    """

    title = models.CharField(
        "Название",
        max_length=150,
        blank=True,
        null=True,
    )
    name = models.CharField(
        "Внешнее имя",
        max_length=150,
        blank=True,
        null=True,
    )
    _id = models.IntegerField(
        "Внешний ID",
        blank=True,
        null=True,
    )
    full_name = models.CharField(
        "Полное внешнее имя",
        max_length=255,
        blank=True,
        null=True,
    )
    code = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.CASCADE,
        related_name="region_sights",
    )
    query = models.CharField("Строка поиска", max_length=150, blank=True)
    query_additional = models.CharField(
        "Дополнительные строки поиска",
        max_length=255,
        help_text="через запятую",
        blank=True,
        null=True,
    )
    kernel = models.JSONField(
        "Семантическое ядро", max_length=500, default=list, blank=True
    )
    rate = models.FloatField(
        verbose_name="Рейтинг",
        default=0.0,
    )
    stars = models.IntegerField(
        verbose_name="Звезды",
        default=0,
    )
    viewings = models.IntegerField(
        verbose_name="Количество просмотров",
        default=0,
    )
    lat = models.FloatField(
        verbose_name="Широта",
        default=0.0,
    )
    lon = models.FloatField(
        verbose_name="Долгота",
        default=0.0,
    )
    group = models.ForeignKey(
        SightGroup,
        verbose_name="Группы",
        related_name="group_sights",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
    )
    city = models.ForeignKey(
        City,
        verbose_name="Город",
        on_delete=models.CASCADE,
        related_name="city_sights",
        blank=True,
        null=True,
    )
    address = models.CharField("Адрес", max_length=255, blank=True, null=True)
    _address = models.CharField("Внешний адрес", max_length=255, blank=True, null=True)
    full_link = models.CharField("Ссылка", max_length=500, blank=True, null=True)
    photo = models.CharField("Фото", max_length=500, blank=True, null=True)
    operating_hours = models.CharField(
        "Часы работы", max_length=700, blank=True, null=True
    )
    operating_hours_data = models.CharField(
        "Дополнительная информация о часах работы",
        max_length=700,
        blank=True,
        null=True,
    )
    is_checked = models.BooleanField(
        "Запрос проверен",
        default=False,
        db_index=True,
    )
    modified_kernel = models.DateTimeField(
        "Последнее обновление ядра", blank=True, null=True
    )
    is_pub = models.BooleanField(
        "Публиковать",
        default=False,
        db_index=True,
    )
    is_in_geo_region = models.BooleanField(default=True)
    geo_data = models.JSONField(default=dict, blank=True)
    objects = models.Manager()
    pub = PubManager()

    def __str__(self):
        return f"{ self.title or ''}"

    class Meta:
        verbose_name = "Достопримечательность"
        verbose_name_plural = "Достопримечательности"
        unique_together = (
            ["name", "full_name", "city", "is_pub", "code", "lat", "lon"],
        )
        ordering = ("title",)


def update_modified_kernel(sender, instance, *args, **kwargs) -> None:
    """
    Updates modified kernel if required
    :param sender: Sight
    :param instance: Sight
    :return: None
    """
    if instance.pk:
        try:
            old = Sight.objects.get(pk=instance.pk)
            if old.kernel != instance.kernel:
                instance.modified_kernel = timezone.now()
        except Sight.DoesNotExist:
            pass


def fill_geo_data(sender, instance, *args, **kwargs) -> None:
    try:
        from acesta_updater.management.commands.helpers.sight_helper import (
            get_geo_data,
            get_address,
            check_region,
            get_city,
            get_query,
        )

        if instance.pk:
            try:
                old = Sight.objects.get(pk=instance.pk)
                if old.lat != instance.lat or old.lon != instance.lon:
                    instance.geo_data = get_geo_data(instance.lon, instance.lat)
                    instance.address = get_address(instance.geo_data)
                    instance.city = get_city(instance.geo_data)
            except Sight.DoesNotExist:
                pass

            if not instance.geo_data:
                instance.geo_data = get_geo_data(instance.lon, instance.lat)
            instance.is_in_geo_region = check_region(instance.code, instance.geo_data)

            if len(instance.query) < 2:
                instance.query = get_query(instance.title or instance.name)

        else:

            instance.geo_data = get_geo_data(instance.lon, instance.lat)
            instance.address = get_address(instance.geo_data)
            instance.city = get_city(instance.geo_data)

            if not check_region(instance.code, instance.geo_data):
                instance.geo_data = False

    except ImportError:
        pass


models.signals.pre_save.connect(update_modified_kernel, sender=Sight)
models.signals.pre_save.connect(fill_geo_data, sender=Sight)
