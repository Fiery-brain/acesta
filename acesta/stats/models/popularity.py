from django.db import models

from acesta.geo.models import City
from acesta.geo.models import Region
from acesta.geo.models import Sight
from acesta.stats.models.abstract import CityPopularity
from acesta.stats.models.abstract import RegionPopularity
from acesta.stats.models.abstract import SightGroupMixin
from acesta.stats.models.abstract import StorageMixin
from acesta.stats.models.abstract import TourismTypeMixin


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
