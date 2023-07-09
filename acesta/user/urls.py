from importlib import import_module

from allauth.account.views import account_inactive
from allauth.account.views import confirm_email
from allauth.account.views import email_verification_sent
from allauth.account.views import login
from allauth.account.views import logout
from allauth.account.views import password_reset
from allauth.account.views import password_reset_done
from allauth.account.views import password_reset_from_key
from allauth.account.views import password_reset_from_key_done
from allauth.socialaccount import providers
from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from allauth.socialaccount.views import login_cancelled
from allauth.socialaccount.views import login_error
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls import re_path

from acesta.account.views import email_change
from acesta.account.views import password_change
from acesta.account.views import password_set
from acesta.account.views import signup
from acesta.socialaccount.providers.leaderid.provider import LeaderIDProvider
from acesta.socialaccount.views import connections
from acesta.socialaccount.views import social_signup
from acesta.user.views import get_costs
from acesta.user.views import new_order
from acesta.user.views import offer
from acesta.user.views import offer_report
from acesta.user.views import price
from acesta.user.views import support
from acesta.user.views import user_profile
from acesta.user.views import visitor_request

urlpatterns = [
    path("signup/", signup, name="account_signup"),
    path("login/", login, name="account_login"),
    path("logout/", logout, name="account_logout"),
    path(
        "password-change/",
        password_change,
        name="account_change_password",
    ),
    path("password/set/", password_set, name="account_set_password"),
    path("inactive/", account_inactive, name="account_inactive"),
    # E-mail
    path("email-change/", email_change, name="account_change_email"),
    path(
        "confirm-email/",
        email_verification_sent,
        name="account_email_verification_sent",
    ),
    re_path(
        r"^confirm-email/(?P<key>[-:\w]+)/$",
        confirm_email,
        name="account_confirm_email",
    ),
    # password reset
    path("password/reset/", password_reset, name="account_reset_password"),
    path(
        "password/reset/done/",
        password_reset_done,
        name="account_reset_password_done",
    ),
    re_path(
        r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        password_reset_from_key,
        name="account_reset_password_from_key",
    ),
    path(
        "password/reset/key/done/",
        password_reset_from_key_done,
        name="account_reset_password_from_key_done",
    ),
]

urlpatterns += [
    path(
        "login/cancelled/",
        login_cancelled,
        name="socialaccount_login_cancelled",
    ),
    path("login/error/", login_error, name="socialaccount_login_error"),
    path("social-signup/", social_signup, name="socialaccount_signup"),
    path("connections/", connections, name="socialaccount_connections"),
]

# Provider urlpatterns, as separate attribute (for reusability).
provider_urlpatterns = []
for provider in providers.registry.get_list():
    try:
        prov_mod = import_module(provider.get_package() + ".urls")
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, "urlpatterns", None)
    if prov_urlpatterns:
        provider_urlpatterns += prov_urlpatterns
urlpatterns += provider_urlpatterns
urlpatterns += default_urlpatterns(LeaderIDProvider)

urlpatterns += [
    path("user/<str:code>/", login_required(user_profile), name="user"),
    path("user/", login_required(user_profile), name="user"),
    path("price/", login_required(price), name="price"),
    path("request/", visitor_request, name="visitor_request"),
    path("support/", login_required(support), name="support"),
    path("offer/", login_required(offer), name="offer"),
    path("offer_report/", login_required(offer_report), name="offer_report"),
    path("new_order/", login_required(new_order), name="order"),
    path("get_costs/", login_required(get_costs), name="costs"),
]
