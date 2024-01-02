import environ
from django.contrib import admin

from acesta.stats.models import AllCityPopularity
from acesta.stats.models import AllRegionPopularity
from acesta.stats.models import CityCityPopularity
from acesta.stats.models import CityRegionPopularity
from acesta.stats.models import RegionCityPopularity
from acesta.stats.models import RegionRegionPopularity

env = environ.Env()


@admin.register(AllCityPopularity)
class AllCityPopularityAdmin(admin.ModelAdmin):
    """
    Популярность в городах
    """

    readonly_fields = (
        "sight",
        "home_code",
        "source_code",
        "code",
        "sight_group",
    )
    list_filter = (
        "sight_group",
        "source_code",
    )
    list_display = (
        "sight",
        "home_code",
        "code",
        "qty",
        "popularity_mean",
        "popularity_mean_all",
        "popularity_max",
        "date",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CityCityPopularity)
class CityCityPopularityAdmin(admin.ModelAdmin):
    """
    Популярность городов в других городах
    """

    readonly_fields = (
        "home_code",
        "code",
        "tourism_type",
    )
    list_filter = (
        "tourism_type",
        "home_code__code",
    )
    list_display = (
        "home_code",
        "code",
        "qty",
        "popularity_mean",
        "popularity_mean_all",
        "popularity_max",
        "date",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(RegionCityPopularity)
class RegionCityPopularityAdmin(admin.ModelAdmin):
    """
    Популярность регионов в городах
    """

    readonly_fields = (
        "home_code",
        "code",
        "tourism_type",
    )
    list_filter = (
        "tourism_type",
        "home_code",
    )
    list_display = (
        "home_code",
        "code",
        "qty",
        "popularity_mean",
        "popularity_mean_all",
        "popularity_max",
        "date",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CityRegionPopularity)
class CityRegionPopularityAdmin(admin.ModelAdmin):
    """
    Популярность городов в регионах
    """

    readonly_fields = (
        "home_code",
        "code",
        "tourism_type",
    )
    list_filter = (
        "tourism_type",
        "home_code__code",
    )
    list_display = (
        "home_code",
        "code",
        "qty",
        "popularity_mean",
        "popularity_mean_all",
        "popularity_max",
        "date",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AllRegionPopularity)
class AllRegionPopularity(admin.ModelAdmin):
    """
    Популярность в регионах
    """

    readonly_fields = (
        "sight",
        "home_code",
        "code",
        "sight_group",
    )
    list_filter = (
        "sight_group",
        "home_code",
    )
    list_display = (
        "sight",
        "home_code",
        "code",
        "qty",
        "popularity_mean",
        "popularity_mean_all",
        "popularity_max",
        "date",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(RegionRegionPopularity)
class RegionRegionPopularityAdmin(admin.ModelAdmin):
    """
    Популярность регионов в других регионах
    """

    readonly_fields = (
        "home_code",
        "tourism_type",
    )
    list_filter = (
        "tourism_type",
        "home_code",
    )
    list_display = (
        "home_code",
        "code",
        "qty",
        "popularity_mean",
        "popularity_mean_all",
        "popularity_max",
        "date",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False
