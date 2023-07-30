from allauth.account.forms import PasswordField
from allauth.account.forms import SignupForm as BaseSignupForm
from allauth.account.forms import UserForm
from allauth.account.utils import get_adapter
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class SignupForm(BaseSignupForm, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].required = False

    class Meta:
        model = User
        fields = (
            "first_name",
            "phone",
        )


class SignupNextForm(forms.ModelForm):
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["password1"] = PasswordField(
            label=_("Password"), autocomplete="new-password"
        )

    def clean(self):
        super().clean()
        password = self.cleaned_data.get("password1")
        if password:
            try:
                get_adapter().clean_password(password, user=self.user)
            except forms.ValidationError as e:
                self.add_error("password1", e)

    class Meta:
        model = User
        fields = (
            "region",
            "purpose",
            "subscription",
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
