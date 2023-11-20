import re

from allauth.account.utils import perform_login
from allauth.account.utils import user_field
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.urls import reverse

from acesta.geo.models import City
from acesta.geo.models import Region

User = get_user_model()


def user_phone(user, *args):
    """
    Sets phone
    :param user: object
    :param args: list
    :return: None
    """
    if args[0]:
        user_field(user, "phone", re.sub(r"[^\d]", "", args[0]))


def user_region(user, *args):
    """
    Sets region
    :param user: object
    :param args: list
    :return: None
    """
    try:
        region = Region.objects.get(title__startswith=args[0].split(" ")[0])
    except Region.MultipleObjectsReturned:
        try:
            region = Region.objects.get(title=args[0])
        except Region.DoesNotExist:
            return
    except Region.DoesNotExist:
        return
    setattr(user, "region", region)


def user_city(user, *args):
    """
    Set city
    :param user: object
    :param args: list
    :return: None
    """
    try:
        city = City.objects.get(title=args[0])
    except Region.DoesNotExist:
        return
    setattr(user, "city", city)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Social Account Adapter Class
    """

    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user
        if user.id:
            return
        try:
            # if user exists, connect the account to the existing account and login
            customer = User.objects.get(email=user.email)
            sociallogin.state["process"] = "connect"
            perform_login(request, customer, "none")
        except User.DoesNotExist:
            pass

    def populate_user(self, request, sociallogin, data):
        """
        Instantiates and populates a `SocialLogin` model based on the data
        retrieved in `response`. The method does NOT save the model to the
        DB.
        """
        user = super().populate_user(request, sociallogin, data)
        user_field(user, "middle_name", data.get("middle_name"))
        user_field(user, "company", data.get("company"))
        user_field(user, "position", data.get("position"))
        user_phone(user, data.get("phone"))
        if data.get("region"):
            user_region(user, data.get("region"))
        if data.get("city"):
            user_city(user, data.get("city"))
        return user

    def get_connect_redirect_url(self, request, socialaccount):
        """
        Returns the default URL to redirect to after successfully
        connecting a social account.
        """
        assert request.user.is_authenticated
        url = reverse("user")
        return url

    def get_signup_form_initial_data(self, sociallogin):
        """
        Returns Signup Form initial data
        :param sociallogin: object
        :return: dict
        """
        initial = super().get_signup_form_initial_data(sociallogin)
        user = sociallogin.user
        initial.update(
            dict(
                middle_name=user_field(user, "middle_name") or "",
                company=user_field(user, "company") or "",
                position=user_field(user, "position") or "",
                phone=user_field(user, "phone") or "",
            )
        )
        if hasattr(user, "region"):
            initial.update(
                dict(
                    region=getattr(user, "region"),
                )
            )
        if hasattr(user, "city"):
            initial.update(
                dict(
                    city=getattr(user, "city"),
                )
            )
        return initial

    def save_user(self, request, sociallogin, form=None):
        """
        Saves a newly signed up social login. In case of auto-signup,
        the signup form is not available
        :param request: django.http.HTTPRequest
        :param sociallogin: allauth.account.models.SocialLogin
        :param form: django.Form
        :return: acesta.user.models.User
        """
        user_field(sociallogin.user, "middle_name", request.POST.get("middle_name", ""))
        user_field(sociallogin.user, "company", request.POST.get("company"), "")
        user_field(sociallogin.user, "position", request.POST.get("position"), "")
        user_field(sociallogin.user, "phone", request.POST.get("phone"), "")
        user_field(sociallogin.user, "region_id", request.POST.get("region"))
        user_field(sociallogin.user, "city_id", request.POST.get("city"))
        return super().save_user(request, sociallogin, form)
