from django.conf import settings
from django.db import models

from acesta.geo.models import City
from acesta.geo.models import Region


def get_object_title(pk: str, area: str) -> models.Model:
    """
    Returns object title by primary key and area
    :param pk: str
    :param area: str
    :return:
    """
    object_model = Region if area == settings.AREA_REGIONS else City
    return getattr(object_model.objects.get(pk=pk), "title")
