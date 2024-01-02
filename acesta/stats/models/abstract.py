from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel

from acesta.geo.models import City
from acesta.geo.models import Region
from acesta.geo.models import SightGroup


class HistoryMixin(models.Model):
    """
    History mixin
    """

    history = models.JSONField(
        "История",
        max_length=2500,
        default=list,
    )

    class Meta:
        abstract = True


class StorageMixin(models.Model):
    """
    Storage mixin
    """

    storage = models.JSONField(
        "Временное хранилище",
        max_length=2500,
        default=dict,
    )

    class Meta:
        abstract = True


class Popularity(TimeStampedModel, HistoryMixin):
    """
    Abstract popularity
    """

    date = models.DateTimeField("Дата", null=True, blank=True)
    qty = models.IntegerField(
        "Показы", default=0, help_text="Среднее число показов в месяц", db_index=True
    )
    popularity_mean_all = models.FloatField(
        "Популярность",
        default=0,
        help_text="Средняя региональная популярность в геообъекте по всем запросам",
    )
    popularity_mean = models.FloatField(
        "Популярность > 100",
        default=0,
        help_text="Средняя региональная популярность в геообъекте только по запросам, вызвавшим интерес",
    )
    popularity_max = models.FloatField(
        "Максимальная популярность",
        default=0,
        help_text="Максимальная региональная популярность в геообъекте",
    )

    class Meta:
        abstract = True


class CityPopularity(Popularity):
    """
    Abstract popularity in cities
    """

    code = models.ForeignKey(
        City,
        verbose_name="Интересант",
        on_delete=models.CASCADE,
        related_name="city_%(class)s",
    )

    class Meta:
        abstract = True


class RegionPopularity(Popularity):
    """
    Abstract popularity in regions
    """

    code = models.ForeignKey(
        Region,
        verbose_name="Интересант",
        on_delete=models.CASCADE,
        related_name="region_%(class)s",
    )

    class Meta:
        abstract = True


class SightGroupMixin(models.Model):
    """
    Sight group mixin
    """

    sight_group = models.ForeignKey(
        SightGroup,
        verbose_name="Вид достопримечательности",
        on_delete=models.DO_NOTHING,
        related_name="group_%(class)s",
        max_length=15,
        blank=True,
        null=True,
        db_index=True,
    )

    class Meta:
        abstract = True


class TourismTypeMixin(models.Model):
    """
    Tourism type mixin
    """

    tourism_type = models.CharField(
        "Вид туризма",
        max_length=10,
        choices=settings.TOURISM_TYPES,
        blank=True,
        null=True,
        db_index=True,
    )

    class Meta:
        abstract = True


class Audience(TimeStampedModel, HistoryMixin, TourismTypeMixin):
    """
    Abstract audience
    """

    date = models.DateField(auto_now=True)
    code = models.CharField(max_length=20)
    sex = models.CharField("Пол", max_length=1, choices=settings.SEX)
    age = models.CharField("Возраст", max_length=5, choices=settings.AGE)
    v_all = models.IntegerField("Общее число по региону", default=0)
    v_types = models.IntegerField("Общее число заинтересованных в туризме", default=0)
    v_type_sex_age = models.IntegerField(
        "Заинтересованные, разбивка: вид туризма, пол, возраст", default=0
    )
    v_sex_age = models.IntegerField("Число определенного пола и возраста", default=0)
    v_sex_age_child_6 = models.IntegerField(
        "Число определенного пола и возраста с детьми до 6 лет", default=0
    )
    v_sex_age_child_7_12 = models.IntegerField(
        "Число определенного пола и возраста с детьми от 7 до 12 лет", default=0
    )
    v_sex_age_parents = models.IntegerField(
        "Число определенного пола и возраста с родителями", default=0
    )
    v_type_in_pair = models.IntegerField(
        "Число определенного пола и возраста с интересом к виду туризма и в паре",
        default=0,
    )
    coeff = models.FloatField("Восстанавливающий коэффициент", default=1)

    class Meta:
        abstract = True


class Rating(TimeStampedModel, HistoryMixin):
    """
    Abstract rating
    """

    date = models.DateField("Дата", auto_now=True)
    rating_type = models.CharField(
        "Вид рейтинга",
        max_length=10,
        choices=settings.RATING_TYPES,
        default=settings.RATING_TYPE_DEFAULT,
    )
    place = models.IntegerField("Место", default=0)
    region_code = models.ForeignKey(
        Region,
        verbose_name="Регион-интересант",
        on_delete=models.CASCADE,
        related_name="region_%(class)s",
        blank=True,
        null=True,
    )
    city_code = models.ForeignKey(
        City,
        verbose_name="Город-интересант",
        on_delete=models.CASCADE,
        related_name="city_%(class)s",
        blank=True,
        null=True,
    )

    value = models.IntegerField(
        "Значение",
        default=0,
        blank=True,
        null=True,
    )

    class Meta:
        abstract = True
