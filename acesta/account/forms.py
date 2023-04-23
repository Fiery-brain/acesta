from allauth.account.forms import PasswordField
from allauth.account.forms import SignupForm as BaseSignupForm
from allauth.account.forms import UserForm
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class SignupForm(BaseSignupForm, forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "last_name",
            "first_name",
            "middle_name",
            "region",
            "city",
            "position",
            "company",
            "phone",
        )


class ChangeEmailForm(UserForm):

    email = forms.EmailField(required=True)

    oldpassword = PasswordField(
        label=_("Current Password"), autocomplete="current-password"
    )

    def clean_email(self):
        try:
            User.objects.get(email=self.cleaned_data.get("email"))
            raise forms.ValidationError("Такой email уже существует")
        except User.DoesNotExist:
            return self.cleaned_data["email"]

    def clean_oldpassword(self):
        if not self.user.check_password(self.cleaned_data.get("oldpassword")):
            raise forms.ValidationError("Текущий пароль введен неверно")
        return self.cleaned_data["oldpassword"]

    def save(self):
        self.user.email = self.cleaned_data["email"]
        self.user.save(update_fields=["email"])
