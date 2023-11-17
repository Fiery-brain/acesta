from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel

from acesta.geo.models import City
from acesta.geo.models import Region
from acesta.geo.models import Sight
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


class AllCityPopularity(CityPopularity, StorageMixin, SightGroupMixin):
    """
    Popularity in cities
    """

    sight = models.ForeignKey(
        Sight,
        verbose_name="Достопримечательность",
        on_delete=models.CASCADE,
        related_name="sight_all_city_popularity",
        blank=True,
        null=True,
    )
    home_code = models.ForeignKey(
        City,
        verbose_name="Город",
        on_delete=models.CASCADE,
        related_name="home_city_all_city_popularity",
        blank=True,
        null=True,
    )
    source_code = models.ForeignKey(
        Region,
        verbose_name="Регион-источник",
        on_delete=models.CASCADE,
        related_name="source_region_all_city_popularity",
    )

    class Meta:
        ordering = ("-qty",)
        verbose_name = "Вся популярность в городах"
        verbose_name_plural = "Вся популярность в городах"
        unique_together = ("sight", "home_code", "code", "source_code", "sight_group")


class AllRegionPopularity(RegionPopularity, StorageMixin, SightGroupMixin):
    """
    Popularity in regions
    """

    sight = models.ForeignKey(
        Sight,
        verbose_name="Достопримечательность",
        on_delete=models.CASCADE,
        related_name="sight_all_region_popularity",
        blank=True,
        null=True,
    )
    home_code = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.CASCADE,
        related_name="home_region_all_region_popularity",
    )
    source_city = models.ForeignKey(
        City,
        verbose_name="Город-источник",
        on_delete=models.CASCADE,
        related_name="source_city_all_region_popularity",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ("-qty",)
        verbose_name = "Вся популярность в регионах"
        verbose_name_plural = "Вся популярность в регионах"
        unique_together = ("sight", "home_code", "code", "source_city", "sight_group")


class RegionRegionPopularity(RegionPopularity, TourismTypeMixin):
    """
    Regions popularity in regions
    """

    home_code = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.CASCADE,
        related_name="home_region_region_popularities",
    )

    class Meta:
        ordering = ("-qty", "code")
        indexes = [
            models.Index(fields=["home_code", "tourism_type", "qty", "code"]),
        ]
        verbose_name = "Популярность регионов в регионах"
        verbose_name_plural = "Популярность регионов в регионах"
        unique_together = (
            "home_code",
            "code",
            "tourism_type",
        )


class RegionCityPopularity(CityPopularity, TourismTypeMixin):
    """
    Regions popularity in cities
    """

    home_code = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.CASCADE,
        related_name="home_region_city_popularities",
    )

    class Meta:
        ordering = ("-qty", "code")
        indexes = [
            models.Index(fields=["home_code", "tourism_type", "qty", "code"]),
        ]
        verbose_name = "Популярность регионов в городах"
        verbose_name_plural = "Популярность регионов в городах"
        unique_together = (
            "home_code",
            "code",
            "tourism_type",
        )


class CityRegionPopularity(RegionPopularity, TourismTypeMixin):
    """
    Cities popularity in regions
    """

    home_code = models.ForeignKey(
        City,
        verbose_name="Город",
        on_delete=models.CASCADE,
        related_name="home_city_region_popularities",
    )

    class Meta:
        ordering = ("-qty", "code")
        indexes = [
            models.Index(fields=["home_code", "tourism_type", "qty", "code"]),
        ]
        verbose_name = "Популярность городов в регионах"
        verbose_name_plural = "Популярность городов в регионах"
        unique_together = (
            "home_code",
            "code",
            "tourism_type",
        )


class CityCityPopularity(CityPopularity, TourismTypeMixin):
    """
    Cities popularity in cities
    """

    home_code = models.ForeignKey(
        City,
        verbose_name="Город",
        on_delete=models.CASCADE,
        related_name="home_city_city_popularities",
    )

    class Meta:
        ordering = ("-qty", "code")
        indexes = [
            models.Index(fields=["home_code", "tourism_type", "qty", "code"]),
        ]
        verbose_name = "Популярность городов в городах"
        verbose_name_plural = "Популярность городов в городах"
        unique_together = (
            "home_code",
            "code",
            "tourism_type",
        )


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


class RegionRating(Rating, TourismTypeMixin):
    """
    Regions rating
    """

    home_code = models.ForeignKey(
        Region,
        verbose_name="Домашний регион",
        on_delete=models.CASCADE,
        related_name="home_region_regionratings",
    )

    class Meta:
        unique_together = (
            "rating_type",
            "home_code",
            "region_code",
            "city_code",
        )
        indexes = [
            models.Index(
                fields=[
                    "region_code",
                    "tourism_type",
                    "rating_type",
                    "place",
                ]
            )
        ]
        ordering = (
            "rating_type",
            "place",
        )
        verbose_name = "Рейтинг регионов"
        verbose_name_plural = "Рейтинг регионов"


class CityRating(Rating, TourismTypeMixin):
    """
    Cities rating
    """

    home_code = models.ForeignKey(
        City,
        verbose_name="Домашний город",
        on_delete=models.CASCADE,
        related_name="home_city_cityratings",
    )
    home_region = models.ForeignKey(
        Region,
        verbose_name="Домашний регион",
        on_delete=models.CASCADE,
        related_name="home_region_cityratings",
        blank=True,
        null=True,
    )

    class Meta:
        unique_together = (
            "rating_type",
            "home_code",
            "region_code",
            "city_code",
        )
        indexes = [
            models.Index(
                fields=[
                    "home_region",
                    "tourism_type",
                    "rating_type",
                    "place",
                ]
            )
        ]
        ordering = (
            "rating_type",
            "place",
        )
        verbose_name = "Рейтинг городов"
        verbose_name_plural = "Рейтинг городов"


class SightRating(Rating, SightGroupMixin):
    """
    Sights rating
    """

    sight = models.ForeignKey(
        Sight,
        verbose_name="Достопримечательность",
        on_delete=models.CASCADE,
        related_name="sight_ratings",
    )

    class Meta:
        unique_together = (
            "rating_type",
            "sight",
            "region_code",
            "city_code",
        )
        indexes = [
            models.Index(
                fields=[
                    "region_code",
                    "sight_group",
                    "rating_type",
                    "place",
                ]
            )
        ]
        ordering = (
            "rating_type",
            "place",
        )
        verbose_name = "Рейтинг достопримечательностей"
        verbose_name_plural = "Рейтинг достопримечательностей"


class Salary(TimeStampedModel):
    """
    Regions salary
    """

    code = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.CASCADE,
        related_name="region_salaries",
    )
    value_type = models.CharField(
        "Вид показателя",
        choices=settings.SALARY_TYPES,
        default=settings.SALARY_TYPE_DEFAULT,
        max_length=30,
    )
    quarter = models.PositiveSmallIntegerField(
        "Квартал", choices=((q, q) for q in range(1, 5))
    )
    year = models.PositiveSmallIntegerField(
        "Год", choices=((y, y) for y in range(2019, 2031, 1))
    )
    value = models.FloatField("Значение", default=0.0)

    class Meta:
        unique_together = (
            "code",
            "value_type",
            "quarter",
            "year",
        )
        indexes = [
            models.Index(fields=["value_type", "quarter", "year"]),
        ]
        ordering = (
            "-year",
            "-quarter",
            "code",
        )
        verbose_name = "Доходы"
        verbose_name_plural = "Доходы"
