from django import forms
from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from acesta.user.models import Order
from acesta.user.models import Region
from acesta.user.models import Request
from acesta.user.models import Support

User = get_user_model()


class UserForm(forms.ModelForm):
    """
    User's data Form
    """

    class Meta:
        model = User
        fields = [
            "last_name",
            "first_name",
            "middle_name",
            "company",
            "position",
            "phone",
            "city",
        ]


class ExtendedRegionsField(forms.ModelMultipleChoiceField):
    """
    A MultipleChoiceField with extended labels
    """

    def label_from_instance(self, obj) -> str:
        """
        Extents getting a label
        :param obj: Region
        :return: str
        """
        return f"{obj.title} ({obj.rank} ранг)"


class OrderForm(forms.ModelForm):
    """
    New Order Form
    """

    regions = ExtendedRegionsField(queryset=Region.pub.all())

    class Meta:
        model = Order
        fields = [
            "regions",
            "period",
            "user",
        ]


class SupportForm(forms.ModelForm):
    """
    Support Form
    """

    class Meta:
        model = Support
        fields = [
            "message",
            "subject",
            "user",
        ]


class RequestForm(forms.ModelForm):
    """
    Request Form
    """

    class Meta:
        model = Request
        fields = [
            "name",
            "user",
            "subject",
            "channel",
            "time",
            "_id",
            "comment",
        ]


class UserCreationForm(admin_forms.UserCreationForm):

    error_message = admin_forms.UserCreationForm.error_messages.update(
        {"duplicate_username": _("This username has already been taken.")}
    )

    class Meta(admin_forms.UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise ValidationError(self.error_messages["duplicate_username"])
