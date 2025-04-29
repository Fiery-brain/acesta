from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel

from acesta.base.managers import PubManager
from acesta.geo.utils import fill_geo_data
from acesta.geo.utils import update_modified_kernel


class Region(TimeStampedModel):
    """
    Region model
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
    federal_district = models.CharField(
        "Федеральный округ", max_length=4, choices=settings.FEDERAL_DISTRICTS
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
    is_pub = models.BooleanField("Публиковать", default=False, db_index=True)
    objects = models.Manager()
    pub = PubManager()

    @property
    def region_short(self):
        return self.title.split(" - ")[0]

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"
        ordering = ("title",)


class City(TimeStampedModel):
    """
    City model
    """

    code = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.CASCADE,
        related_name="region_cities",
    )
    _id = models.IntegerField("Внешний ID", unique=True)
    title = models.CharField("Название", max_length=150, db_index=True)
    area = models.CharField(
        "Район",
        max_length=150,
        blank=True,
        null=True,
    )
    lat = models.FloatField(verbose_name="Широта", default=0.0)
    lon = models.FloatField(verbose_name="Долгота", default=0.0)
    population = models.IntegerField("Численность", default=0)
    foundation = models.CharField(
        "Год основания",
        max_length=60,
    )
    is_capital = models.BooleanField("Столица", default=False)
    is_pub = models.BooleanField("Публиковать", default=False, db_index=True)
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
    Sight group model
    """

    tourism_type = models.CharField(
        "Вид туризма",
        max_length=10,
        choices=settings.TOURISM_TYPES,
        default=settings.TOURISM_TYPE_DEFAULT,
    )
    name = models.CharField("Имя", max_length=25, primary_key=True)
    title = models.CharField("Название", max_length=150)
    title_gen = models.CharField(
        "Название в родительном падеже",
        max_length=150,
    )
    is_pub = models.BooleanField("Публиковать", default=False, db_index=True)
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
    Sight model
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
    lat = models.FloatField(verbose_name="Широта", default=0.0)
    lon = models.FloatField(verbose_name="Долгота", default=0.0)
    group = models.ManyToManyField(
        SightGroup,
        verbose_name="Группы",
        related_name="group_sights",
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
    is_checked = models.BooleanField("Запрос проверен", default=False, db_index=True)
    is_network = models.BooleanField("Сеть", default=False, db_index=True)
    is_archive = models.BooleanField("Архив", default=False, db_index=True)
    similarity_rate = models.FloatField(
        verbose_name="Схожесть запроса и ядра", default=0.0
    )
    is_kernel_checked = models.BooleanField(
        "Ядро проверено", default=False, db_index=True
    )
    modified_kernel = models.DateTimeField(
        "Последнее обновление ядра", blank=True, null=True
    )
    is_pub = models.BooleanField("Публиковать", default=False, db_index=True)
    is_in_geo_region = models.BooleanField(default=True)
    geo_data = models.JSONField(default=dict, blank=True)
    additional_data = models.JSONField(default=dict, blank=True)
    objects = models.Manager()
    pub = PubManager()

    def __str__(self):
        return f"{ self.title or ''}"

    class Meta:
        verbose_name = "Достопримечательность"
        verbose_name_plural = "Достопримечательности"
        unique_together = (
            [
                "name",
                "full_name",
                "city",
                "is_pub",
                "code",
                "lat",
                "lon",
                "is_network",
                "is_archive",
            ],
        )
        ordering = ("title",)


models.signals.pre_save.connect(update_modified_kernel, sender=Sight)
models.signals.pre_save.connect(fill_geo_data, sender=Sight)
