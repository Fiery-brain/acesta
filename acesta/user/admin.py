from allauth.account.adapter import get_adapter
from allauth.socialaccount.models import SocialAccount
from django import forms
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import forms as admin_forms
from django.db import models
from django.forms import ModelForm
from django_json_widget.widgets import JSONEditorWidget

from acesta.user.forms import UserCreationForm
from acesta.user.models import Order
from acesta.user.models import Request
from acesta.user.models import Support
from acesta.user.models import User

admin.site.unregister(SocialAccount)


class SocialAccountForm(ModelForm):
    """
    Social Accounts form
    """

    class Meta:
        model = SocialAccount
        widgets = {"extra_data": JSONEditorWidget}
        fields = "__all__"


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    """
    Social Accounts management
    """

    form = SocialAccountForm
    search_fields = []
    raw_id_fields = ("user",)
    list_display = (
        "user",
        "uid",
        "provider",
    )
    list_filter = ("provider",)

    def get_search_fields(self, request):
        base_fields = get_adapter().get_user_search_fields()
        return list(map(lambda a: "user__" + a, base_fields))


class UserForm(ModelForm):
    """
    Social Accounts form
    """

    class Meta(admin_forms.UserChangeForm.Meta):
        model = User
        widgets = {
            "period_info": JSONEditorWidget,
            "purpose": forms.Textarea(
                attrs={
                    "style": "width:95%",
                    "rows": 5,
                }
            ),
            "note": forms.Textarea(
                attrs={
                    "style": "width:95%",
                    "rows": 5,
                }
            ),
        }
        fields = "__all__"


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    """
    Users management
    """

    form = UserForm
    add_form = UserCreationForm
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "password",
                    "registered",
                    "is_active",
                    "is_superuser",
                )
            },
        ),
        (
            "Персональная информация",
            {
                "fields": (
                    "last_name",
                    "first_name",
                    "middle_name",
                )
            },
        ),
        (
            "Работа",
            {
                "fields": (
                    "company",
                    "position",
                )
            },
        ),
        (
            "Контакты",
            {
                "fields": (
                    "city",
                    "email",
                    "phone",
                    "purpose",
                    "subscription",
                    "points",
                    "note",
                )
            },
        ),
        (
            "Регионы и виды туризма",
            {
                "fields": (
                    "regions",
                    "region",
                    "current_region",
                    "period_info",
                    "tourism_types",
                )
            },
        ),
        ("Даты", {"fields": ("last_hit", "last_login", "date_joined")}),
    )
    list_display = [
        "first_name",
        "middle_name",
        "last_name",
        "phone",
        "points",
        "registered",
        "purpose",
        "note",
        "region",
        "city",
        "last_hit",
    ]
    search_fields = [
        "username",
        "last_name",
        "region__title",
    ]
    list_filter = (
        "points",
        "region",
        "last_login",
    )

    def get_ordering(self, request):
        return ["-last_hit"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Orders management
    """

    readonly_fields = (
        "cost",
        "total",
    )

    list_display = [
        "order_user",
        "total",
        "order_regions",
        "begin_time",
        "end_time",
        "period",
        "state",
        "created",
        "modified",
    ]

    list_filter = (
        "state",
        "created",
        "modified",
    )

    def order_user(self, obj):
        return f"{obj.user.last_name} {obj.user.first_name} ({obj.user.region})"

    def order_regions(self, obj):
        """
        Returns a list of paid region as a string
        :param obj: Order
        :return: str
        """
        return "\n".join([region.title for region in obj.regions.all()])

    def save_related(self, request, form, formsets, change):
        """
        Given the ``HttpRequest``, the parent ``ModelForm`` instance, the
        list of inline formsets and a boolean value based on whether the
        parent is being added or changed, save the related objects to the
        database. Note that at this point save_form() and save_model() have
        already been called.
        """
        super().save_related(request, form, formsets, change)
        form.save_m2m()
        for formset in formsets:
            self.save_formset(request, form, formset, change=change)

    # def has_delete_permission(self, request, obj=None):
    #     return False


class RequestForm(ModelForm):
    """
    Request form
    """

    class Meta(admin_forms.UserChangeForm.Meta):
        model = Request
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "style": "width:95%",
                    "rows": 5,
                }
            ),
            "note": forms.Textarea(
                attrs={
                    "style": "width:95%",
                    "rows": 5,
                }
            ),
        }
        fields = "__all__"


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    """
    Request Management
    """

    form = RequestForm
    list_display = [
        "name",
        "region",
        "request_user",
        "subject",
        "channel",
        "_id",
        "time",
        "interest",
        "comment",
        "note",
        "state",
        "modified",
    ]

    list_filter = ("subject", "interest", "state", "created", "modified", "region")

    def request_user(self, obj):
        return (
            f"{obj.user.last_name} {obj.user.first_name} ({obj.user.region})"
            if obj.user
            else ""
        )

    # def has_delete_permission(self, request, obj=None):
    #     return False


@admin.register(Support)
class SupportAdmin(admin.ModelAdmin):
    """
    Support Management
    """

    list_display = [
        "support_user",
        "subject",
        "state",
        "created",
        "modified",
    ]

    list_filter = (
        "subject",
        "state",
        "created",
        "modified",
    )

    def support_user(self, obj):
        return f"{obj.user.last_name} {obj.user.first_name} ({obj.user.region})"

    # def has_delete_permission(self, request, obj=None):
    #     return False

    formfield_overrides = {
        models.TextField: {
            "widget": forms.Textarea(
                attrs={
                    "style": "width:80%",
                    "rows": 10,
                }
            )
        },
    }
