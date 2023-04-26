from dadata import Dadata
from django.conf import settings
from httpx import HTTPStatusError
from ipware import get_client_ip

from acesta.geo.models import City
from acesta.geo.models import Region


def get_geo_objects_from_geo_base(request):
    """
    Returns a region code according to the GeoIP base
    :return: str
    """
    region = city = None
    ip, _ = get_client_ip(request)

    try:
        with Dadata(settings.DADATA_TOKEN, settings.DADATA_SECRET) as dadata:

            response = dadata.iplocate(ip).get("data")
            region = Region.objects.filter(
                title__icontains=response.get("region").lower()
            ).first()

            region_filter = dict(code=region) if region else {}
            city = City.objects.filter(
                title=response.get("city"), **region_filter
            ).first()

    except (AttributeError, HTTPStatusError):
        pass

    return region, city
