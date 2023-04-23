from django.conf import settings as django_settings
from django.http import HttpRequest

from acesta.geo.models import Region


def regions(request) -> dict:
    """
    Returns regions grouped by type
    :param request: django.http.HttpRequest
    :return: dict
    """
    result = {}
    if request.user.is_authenticated:
        all_regions = [(region.region_type, region) for region in Region.pub.all()]
        grouped_regions = {}
        for region_type, region in all_regions:
            grouped_regions.setdefault(region_type, []).append(region)
        if "kray" in grouped_regions.keys():
            grouped_regions["kray"] = sorted(
                grouped_regions["kray"], key=lambda x: x.title
            )
        result = {"grouped_regions": grouped_regions}
    return result


def user_region_codes(request: HttpRequest) -> dict:
    """
    Returns user's regions
    :param request: django.http.HttpRequest
    :return: dict
    """
    result = {}
    if request.user.is_authenticated:
        result = {
            "user_regions": [region.code for region in request.user.regions.all()]
        }
    return result


def settings(request: HttpRequest) -> dict:
    """
    Adds settings to context
    :param request: django.http.HttpRequest
    :return: dict
    """
    return dict(
        AREA_REGIONS=django_settings.AREA_REGIONS,
        AREA_CITIES=django_settings.AREA_CITIES,
        AREA_SIGHTS=django_settings.AREA_SIGHTS,
        REGION_TYPE_FEDERAL_CITY=django_settings.REGION_TYPE_FEDERAL_CITY,
    )
