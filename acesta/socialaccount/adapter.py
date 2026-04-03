import json
import re

from allauth.account.utils import perform_login
from allauth.account.utils import user_field
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.urls import reverse

from acesta.geo.models import City
from acesta.geo.models import Region

User = get_user_model()


def get_phone(phone_str):
    return re.sub(r"[^\d]", "", phone_str)


def get_region_by_title(region_str):
    region = None
    try:
        region = Region.objects.get(title__startswith=region_str.split(" ")[0])
    except Region.MultipleObjectsReturned:
        try:
            region = Region.objects.get(title=region_str)
        except Region.DoesNotExist:
            pass
    except (Region.DoesNotExist, AttributeError):
        pass
    return region


def get_city_by_title(city_str):

    city = None
    try:
        city = City.objects.get(title=city_str)
        print(city)
    except City.DoesNotExist:
        pass
    return city


def user_phone(user, *args):
    """
    Sets phone
    :param user: object
    :param args: list
    :return: None
    """
    try:
        user_field(user, "phone", get_phone(args[0]))
    except IndexError:
        pass


def user_region(user, *args):
    """
    Sets region
    :param user: object
    :param args: list
    :return: None
    """
    try:
        region = get_region_by_title(args[0])
        if region is not None:
            setattr(user, "region", region)
    except IndexError:
        pass


def user_city(user, *args):
    """
    Set city
    :param user: object
    :param args: list
    :return: None
    """
    try:
        print(args)
        city = get_city_by_title(args[0])
        if city is not None:
            setattr(user, "city", city)
    except IndexError:
        pass


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
        extra_data = sociallogin.account.extra_data
        initial.update(
            dict(
                phone=extra_data.get("phone"),
                extra_data=json.dumps(
                    dict(
                        last_name=extra_data.get("last_name"),
                        middle_name=extra_data.get("middle_name"),
                        company=extra_data.get("company"),
                        position=extra_data.get("position"),
                        region=extra_data.get("region"),
                        city=extra_data.get("city"),
                    )
                ),
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
        extra_data = json.loads(request.POST.get("extra_data"))
        user_field(
            sociallogin.user, "hidden_last_name", extra_data.get("last_name", "")
        )
        user_field(sociallogin.user, "middle_name", extra_data.get("middle_name", ""))
        user_field(sociallogin.user, "company", extra_data.get("company"), "")
        user_field(sociallogin.user, "position", extra_data.get("position"), "")
        user_field(sociallogin.user, "phone", extra_data.get("phone"), "")
        user_region(sociallogin.user, extra_data.get("region"))
        user_city(sociallogin.user, extra_data.get("city"))
        return super().save_user(request, sociallogin, form)
