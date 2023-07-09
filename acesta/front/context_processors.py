from django.conf import settings as django_settings
from django.http import HttpRequest

from acesta.user.utils import get_request_form


def settings(request: HttpRequest) -> dict:
    """
    Adds settings to context
    :param request: django.http.HttpRequest
    :return: dict
    """
    return dict(
        TITLE=django_settings.TITLE,
        HASH_TAGS=django_settings.HASH_TAGS,
        DEBUG=django_settings.DEBUG,
        REQUEST_CONSULTATION="consultation",
        REQUEST_PRESENTATION="presentation",
        REQUEST_CHANNELS=dict(django_settings.REQUEST_CHANNELS_OUTSIDE),
    )


def request_forms(request: HttpRequest) -> dict:
    """
    Adds request forms to context
    :param request: django.http.HttpRequest
    :return: dict
    """
    return dict(
        consultation_form=get_request_form(
            request.user, django_settings.REQUEST_CONSULTATION
        ),
        presentation_form=get_request_form(
            request.user, django_settings.REQUEST_PRESENTATION
        ),
    )
