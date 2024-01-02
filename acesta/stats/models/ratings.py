from django.db import models

from acesta.geo.models import City
from acesta.geo.models import Region
from acesta.geo.models import Sight
from acesta.stats.models.abstract import Rating
from acesta.stats.models.abstract import SightGroupMixin
from acesta.stats.models.abstract import TourismTypeMixin


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
