from allauth.socialaccount.forms import SignupForm as BaseSocialSignupForm
from django.contrib.auth import get_user_model
from django.forms import ModelForm

User = get_user_model()


class SocialSignupForm(BaseSocialSignupForm, ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "phone",
        )
