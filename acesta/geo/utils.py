from django_ipgeobase.models import IPGeoBase
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
    ip_geo_bases = IPGeoBase.objects.by_ip(ip)
    if ip_geo_bases.exists():
        ip_geo_base = ip_geo_bases[0]
        try:
            region = Region.objects.filter(title=ip_geo_base.region).first()
        except Region.DoesNotExist:
            pass
        try:
            city = City.objects.filter(title=ip_geo_base.city).first()
        except City.DoesNotExist:
            pass
    return region, city
