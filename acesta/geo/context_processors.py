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
        all_regions = [
            (region.federal_district, region)
            for region in Region.pub.all().order_by("code")
        ]
        grouped_regions = {}
        for federal_district, region in all_regions:
            grouped_regions.setdefault(federal_district, []).append(region)
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
        FEDERAL_DISTRICTS=dict(django_settings.FEDERAL_DISTRICTS),
        REGION_TYPE_FEDERAL_CITY=django_settings.REGION_TYPE_FEDERAL_CITY,
    )
