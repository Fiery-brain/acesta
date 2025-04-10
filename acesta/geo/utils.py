# from dadata import Dadata
# from django.conf import settings
from django.utils import timezone

# from httpx import HTTPStatusError
# from ipware import get_client_ip
# from acesta.geo.models import City
# from acesta.geo.models import Region


def get_geo_objects_from_geo_base(request):
    """
    Returns a region code according to the GeoIP base

    Temporarily turned off
    :return: str
    """
    region = city = None
    # ip, _ = get_client_ip(request)
    #
    # try:
    #     with Dadata(settings.DADATA_TOKEN, settings.DADATA_SECRET) as dadata:
    #
    #         response = dadata.iplocate(ip).get("data")
    #         region = Region.objects.filter(
    #             title__icontains=response.get("region").lower()
    #         ).first()
    #
    #         region_filter = dict(code=region) if region else {}
    #         city = City.objects.filter(
    #             title=response.get("city"), **region_filter
    #         ).first()
    #
    # except (AttributeError, HTTPStatusError):
    #     pass

    return region, city


def update_modified_kernel(sender, instance, *args, **kwargs) -> None:
    """
    Updates modified kernel last update date if required
    :param sender: Sight
    :param instance: Sight
    :return: None
    """
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            if old.kernel != instance.kernel:
                instance.modified_kernel = timezone.now()
        except sender.DoesNotExist:
            pass


def fill_geo_data(sender, instance, *args, **kwargs) -> None:
    try:
        from acesta_updater.management.commands.helpers.sight_helper import (
            get_geo_data,
            get_lon_lat,
            get_address,
            check_region,
            get_city,
            get_query,
        )

        def set_instance_geo_data(sight):
            """
            Defines sight geo data by filled data
            :param sight: Sight
            :return: Sight
            """
            if sight.lon and sight.lat:
                sight.geo_data = get_geo_data(sight.lon, sight.lat)
                sight.address = get_address(sight.geo_data)
            elif instance.address:
                sight.geo_data = get_geo_data(sight.lon, sight.lat, sight.address)
                sight.lon, sight.lat = get_lon_lat(sight.geo_data)
                sight.address = get_address(sight.geo_data)

            if sight.geo_data:
                sight.city = get_city(sight.geo_data)
                sight.is_in_geo_region = check_region(sight.code, sight.geo_data)

            return sight

        if instance.pk:
            # try:
            #     old = sender.objects.get(pk=instance.pk)
            #     if (
            #         old.lat != instance.lat
            #         or old.lon != instance.lon
            #         or not instance.geo_data
            #         or old.address != instance.address
            #     ):
            #         instance = set_instance_geo_data(instance)
            # except sender.DoesNotExist:
            #     pass

            if len(instance.query) < 2:
                instance.query = get_query(instance.title or instance.name)

        # else:
        #     instance = set_instance_geo_data(instance)

    except ImportError:
        pass
