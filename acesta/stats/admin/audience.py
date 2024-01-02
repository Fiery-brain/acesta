from django.contrib import admin

from acesta.stats.models import AudienceCities
from acesta.stats.models import AudienceRegions


@admin.register(AudienceCities)
class AudienceCitiesAdmin(admin.ModelAdmin):

    list_filter = (
        "date",
        "tourism_type",
        "code",
    )
    list_display = (
        "tourism_type",
        "code",
        "sex",
        "age",
        "v_all",
        "v_types",
        "v_type_sex_age",
        "modified",
    )

    list_display_links = (
        "tourism_type",
        "code",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AudienceRegions)
class AudienceRegionsAdmin(admin.ModelAdmin):

    list_filter = (
        "date",
        "tourism_type",
        "code",
    )
    list_display = (
        "tourism_type",
        "code",
        "sex",
        "age",
        "v_all",
        "v_types",
        "v_type_sex_age",
        "modified",
    )

    list_display_links = (
        "tourism_type",
        "code",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False
