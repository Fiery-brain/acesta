from django.conf import settings

from acesta.geo.models import City
from acesta.geo.models import Region


def get_object_title(pk: str, area: str) -> str | None:
    """
    Returns object title by primary key and area
    :param pk: str
    :param area: str
    :return:
    """
    object_model = Region if area == settings.AREA_REGIONS else City
    return object_model.objects.filter(pk=pk).values_list("title", flat=True).first()
