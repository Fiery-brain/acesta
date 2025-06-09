from django.conf import settings
from django.db import models

from acesta.base.decorators import to_cache
from acesta.stats.helpers.audience import get_empty_cities
from acesta.stats.models import AllCityPopularity
from acesta.stats.models import AllRegionPopularity
from acesta.stats.models import CityCityPopularity
from acesta.stats.models import CityRegionPopularity
from acesta.stats.models import RegionCityPopularity
from acesta.stats.models import RegionRegionPopularity


def get_interest(
    region: str, home_area: str, interesant_area: str, tourism_type: str, id: int = 0
) -> models.QuerySet:
    """
    Returns interest according to areas
    :param region: str
    :param home_area: str
    :param interesant_area: str
    :param tourism_type: str
    :param id: int
    :return: code
    """

    @to_cache(
        "interest_{region}_{home_area}_{interesant_area}_{tourism_type}_{id}",
        60 * 60 * 24 * 7,
    )
    def _get_interest(**kwargs):

        if home_area == settings.AREA_REGIONS or id == 0:
            ppt_model = (
                RegionRegionPopularity
                if interesant_area == settings.AREA_REGIONS
                else RegionCityPopularity
            )
            return (
                ppt_model.objects.filter(
                    home_code=region,
                    qty__gt=0,
                    **(
                        dict(tourism_type=tourism_type)
                        if tourism_type
                        else dict(tourism_type__isnull=True)
                    )
                )
                .annotate(
                    ppt=models.functions.Round(
                        "popularity_mean", output_field=models.IntegerField()
                    )
                )
                .distinct()
            )
        else:
            if home_area == settings.AREA_CITIES:
                ppt_model = (
                    CityRegionPopularity
                    if interesant_area == settings.AREA_REGIONS
                    else CityCityPopularity
                )
                empty_cities_filter = (
                    dict(code__in=get_empty_cities())
                    if interesant_area == settings.AREA_CITIES
                    else {}
                )
                return (
                    ppt_model.objects.filter(
                        home_code=id,
                        qty__gt=0,
                        **(
                            dict(tourism_type=tourism_type)
                            if tourism_type
                            else dict(tourism_type__isnull=True)
                        )
                    )
                    .exclude(**empty_cities_filter)
                    .annotate(
                        ppt=models.functions.Round(
                            "popularity_mean", output_field=models.IntegerField()
                        )
                    )
                    .distinct()
                )
            elif home_area == settings.AREA_SIGHTS:
                ppt_model = (
                    AllRegionPopularity
                    if interesant_area == settings.AREA_REGIONS
                    else AllCityPopularity
                )
                return (
                    ppt_model.objects.filter(
                        sight__id=id,
                        qty__gt=0,
                    )
                    .annotate(
                        ppt=models.functions.Round(
                            "popularity_mean", output_field=models.IntegerField()
                        )
                    )
                    .distinct()
                )

    return _get_interest(
        region=region,
        home_area=home_area,
        interesant_area=interesant_area,
        tourism_type=tourism_type,
        id=id,
    )
