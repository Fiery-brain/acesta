from django.conf import settings as django_settings
from django.http import HttpRequest


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
    )
