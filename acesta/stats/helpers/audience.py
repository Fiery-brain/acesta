from django.conf import settings
from django.db import models

from acesta.base.decorators import to_cache
from acesta.stats.models import AudienceCities
from acesta.stats.models import AudienceRegions


def get_audience_key_data(key) -> tuple:
    """
    Parses audience key
    :param key: str
    :return: tuple
    """
    return key.split("_") if key else ("01", "", "regions")


def get_audience(area: str, tourism_type: str, code: str) -> models.QuerySet:
    """
    Returns audience according to area and tourism type
    :param area: str
    :param tourism_type: str
    :param code: str
    :return: django.db.models.QuerySet
    """

    @to_cache("audience_{code}_{area}_{tourism_type}", 60 * 60 * 24 * 7)
    def _get_audience(**kwargs):
        tourism_type_filter = (
            dict(tourism_type=tourism_type)
            if tourism_type
            else dict(
                tourism_type__in=list(dict(settings.TOURISM_TYPES_OUTSIDE).keys())
            )
        )
        return (
            (AudienceCities if area == settings.AREA_CITIES else AudienceRegions)
            .objects.filter(
                code_id=(int(code) if area == settings.AREA_CITIES else code),
                **tourism_type_filter
            )
            .order_by("-v_type_sex_age")
        )

    return _get_audience(code=code, area=area, tourism_type=tourism_type)
