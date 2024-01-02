from django.contrib import admin

from acesta.stats.models import Salary


@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    """
    Управление уровнями дохода
    """

    list_filter = (
        "value_type",
        "quarter",
        "year",
        "code",
    )
    list_display = (
        "value_type",
        "code",
        "quarter",
        "year",
        "value",
        "created",
        "modified",
    )

    def has_delete_permission(self, request, obj=None):
        return False
