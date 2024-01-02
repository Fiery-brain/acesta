import math

from django.conf import settings
from django.db import models

from acesta.geo.models import City
from acesta.geo.models import Region
from acesta.stats.models import AudienceCities
from acesta.stats.models import AudienceRegions


def round_up(n, decimals=0) -> int:
    """
    Rounds number up to thousands
    :param n: int
    :param decimals: int
    :return: int
    """
    multiplier = 10**decimals
    return math.ceil(n * multiplier) / multiplier


def get_audience(area: str, tourism_type: str, code: str) -> models.QuerySet:
    """
    Returns audience according to area and tourism type
    :param area: str
    :param tourism_type: str
    :param code: str
    :return: django.db.models.QuerySet
    """
    return (
        (AudienceCities if area == settings.AREA_CITIES else AudienceRegions)
        .objects.filter(
            code_id=int(code) if area == settings.AREA_CITIES else code,
            **(
                dict(tourism_type=tourism_type)
                if tourism_type
                else dict(tourism_type__in=dict(settings.TOURISM_TYPES_OUTSIDE).keys())
            )
        )
        .order_by("-v_type_sex_age")
    )


def get_audience_key_data(key) -> tuple:
    """
    Parses audience key
    :param key: str
    :return: tuple
    """
    return key.split("_") if key else ("01", "", "regions")


def get_object_title(pk: str, area: str) -> models.Model:
    """
    Returns object title by primary key and area
    :param pk: str
    :param area: str
    :return:
    """
    object_model = Region if area == settings.AREA_REGIONS else City
    return getattr(object_model.objects.get(pk=pk), "title")
