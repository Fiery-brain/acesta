from django.contrib import admin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget

from acesta.geo.models import City
from acesta.geo.models import Region
from acesta.geo.models import Sight
from acesta.geo.models import SightGroup


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    """
    Region Management
    """

    search_fields = (
        "code",
        "title",
    )
    list_filter = (
        "region_type",
        "rank",
        "is_pub",
    )

    list_display = (
        "code",
        "title",
        "rank",
        "is_pub",
        "created",
        "modified",
    )

    list_display_links = (
        "code",
        "title",
    )

    readonly_fields = (
        "code",
        "region",
        "title",
        "population",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    """
    City Management
    """

    search_fields = ("title",)

    list_filter = (
        "is_pub",
        "is_capital",
        "code",
    )

    list_display = (
        "title",
        "area",
        "lat",
        "lon",
        "population",
        "is_pub",
    )
    list_display_links = ("title",)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SightGroup)
class SightGroupAdmin(admin.ModelAdmin):
    """
    Sight group Management
    """

    list_display = (
        "tourism_type",
        "name",
        "title",
    )

    list_display_links = ("title",)

    list_filter = (
        "is_pub",
        "tourism_type",
    )


@admin.register(Sight)
class SightAdmin(admin.ModelAdmin):
    """
    Sight Management
    """

    search_fields = ("title",)

    readonly_fields = ["name", "full_name", "_id", "city"]

    list_display = (
        "title",
        "name",
        "query",
        "sight_kernel",
        "sight_groups",
        "city",
        "is_pub",
        "is_checked",
        "created",
        "modified",
    )

    list_display_links = ("title",)

    list_filter = (
        "is_pub",
        "is_checked",
        "group__tourism_type",
        "code",
    )

    def sight_groups(self, obj):
        return [group.title for group in obj.group.all()]

    def sight_kernel(self, obj):
        """
        Returns a list of paid region as a string
        :param obj: Order
        :return: str
        """
        return f"{str(obj.kernel)[:100]}{'...' if len(obj.kernel) > 100 else ''}"

    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
