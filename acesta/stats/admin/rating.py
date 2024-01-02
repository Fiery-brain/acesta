from django.contrib import admin

from acesta.stats.models import CityRating
from acesta.stats.models import RegionRating
from acesta.stats.models import SightRating


@admin.register(CityRating)
class CityRatingAdmin(admin.ModelAdmin):
    """ """

    list_filter = (
        "date",
        "rating_type",
        "home_code__code",
    )
    list_display = (
        "rating_type",
        "home_code",
        "region_code",
        "city_code",
        "place",
        "modified",
    )

    list_display_links = ("home_code",)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(RegionRating)
class RegionRatingAdmin(admin.ModelAdmin):
    """ """

    list_filter = (
        "date",
        "rating_type",
    )
    list_display = (
        "rating_type",
        "home_code",
        "region_code",
        "city_code",
        "place",
        "modified",
    )

    list_display_links = ("home_code",)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SightRating)
class SightRatingAdmin(admin.ModelAdmin):
    """ """

    list_filter = (
        "date",
        "rating_type",
        "sight__group__tourism_type",
        "sight__code",
    )
    list_display = (
        "rating_type",
        "sight",
        "region_code",
        "city_code",
        "place",
        "modified",
    )

    list_display_links = ("sight",)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False
