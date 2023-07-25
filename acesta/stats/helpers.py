import math

import geopandas as gpd
import pandas as pd
from django.conf import settings
from django.db import models

from acesta.geo.models import City
from acesta.geo.models import Region
from acesta.geo.models import Sight
from acesta.stats.models import AllCityPopularity
from acesta.stats.models import AllRegionPopularity
from acesta.stats.models import AudienceCities
from acesta.stats.models import AudienceRegions
from acesta.stats.models import CityCityPopularity
from acesta.stats.models import CityRegionPopularity
from acesta.stats.models import RegionCityPopularity
from acesta.stats.models import RegionRegionPopularity


class GroupConcat(models.Aggregate):
    """
    Aggregate function for JOIN related records
    """

    function = "GROUP_CONCAT"
    template = "%(function)s(%(expressions)s)"

    def __init__(self, expression, delimiter, **extra):
        output_field = extra.pop("output_field", models.CharField())
        delimiter = models.Value(delimiter)
        super(GroupConcat, self).__init__(
            expression, delimiter, output_field=output_field, **extra
        )

    def as_postgresql(self, compiler, connection):
        self.function = "STRING_AGG"
        return super(GroupConcat, self).as_sql(compiler, connection)


def round_up(n, decimals=0) -> int:
    """
    Rounds number up to thousands
    :param n: int
    :param decimals: int
    :return: int
    """
    multiplier = 10**decimals
    return math.ceil(n * multiplier) / multiplier


def get_sight_stats(request) -> list:
    """
    Returns region sight statistics as a list
    :param request: django.http.HttpRequest
    :return: list
    """
    sight_stats = (
        Sight.pub.filter(
            code=request.user.current_region,
        )
        .values("group__tourism_type")
        .annotate(cnt=models.Count("id"), groups=GroupConcat("group__title", "|"))
        .order_by("-cnt")
    )
    sight_stats = [
        {
            "name": stat["group__tourism_type"],
            "title": dict(settings.TOURISM_TYPES_OUTSIDE).get(
                stat["group__tourism_type"]
            ),
            "groups": "<br>".join(sorted(list(set(stat["groups"].split("|"))))),
            "cnt": stat["cnt"],
        }
        for stat in sight_stats
    ]
    return list(sight_stats)


def get_geojson() -> gpd.GeoDataFrame:
    """
    Returns Russia regions geodata
    :return: gpd.GeoDataFrame
    """
    geojson = gpd.read_file(settings.GEOJSON)
    geojson = geojson.set_index("code")
    return geojson


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
    if home_area == settings.AREA_REGIONS or id == 0:
        ppt_model = (
            RegionRegionPopularity
            if interesant_area == settings.AREA_REGIONS
            else RegionCityPopularity
        )
        return ppt_model.objects.filter(
            home_code=region,
            qty__gt=0,
            **dict(tourism_type=tourism_type)
            if tourism_type
            else dict(tourism_type__isnull=True)
        ).annotate(
            ppt=models.functions.Round(
                "popularity_mean", output_field=models.IntegerField()
            )
        )
    else:
        if home_area == settings.AREA_CITIES:
            ppt_model = (
                CityRegionPopularity
                if interesant_area == settings.AREA_REGIONS
                else CityCityPopularity
            )
            return ppt_model.objects.filter(
                home_code=id,
                qty__gt=0,
                **dict(tourism_type=tourism_type)
                if tourism_type
                else dict(tourism_type__isnull=True)
            ).annotate(
                ppt=models.functions.Round(
                    "popularity_mean", output_field=models.IntegerField()
                )
            )
        elif home_area == settings.AREA_SIGHTS:
            ppt_model = (
                AllRegionPopularity
                if interesant_area == settings.AREA_REGIONS
                else AllCityPopularity
            )
            return ppt_model.objects.filter(sight__id=id, qty__gt=0,).annotate(
                ppt=models.functions.Round(
                    "popularity_mean", output_field=models.IntegerField()
                )
            )


def get_ppt_df(ppt_data, sort_by: list) -> pd.DataFrame:
    """
    Returns popularity as a DataFrame
    :param ppt_data
    :return: pd.DataFrame
    """
    columns = (
        "code__title",
        "code",
        "qty",
        "ppt",
    )
    df = pd.DataFrame(list(ppt_data.values(*columns)))
    if not len(df):
        df = pd.DataFrame([["Запрашивают редко", "", "", ""]], columns=columns)
    else:
        df["ppt"] = df["ppt"] / 100

    if len(sort_by):
        df = df.sort_values(
            [sort_by[0]["column_id"], "code"],
            ascending=[(sort_by[0]["direction"] != "asc"), True],
        )
    return df


def get_map_df(tourism_type: str, home_code: str) -> pd.DataFrame:
    """
    Returns map data
    :param tourism_type:
    :param home_code: str
    :return: pd.DataFrame
    """
    df_map = get_geojson()
    ppt_data = (
        RegionRegionPopularity.objects.filter(
            home_code_id=home_code,
            **dict(tourism_type=tourism_type)
            if tourism_type
            else dict(tourism_type__isnull=True)
        )
        .values("code")
        .annotate(qty=models.Sum("qty"), ppt=models.Avg("popularity_mean"))
    )
    df_map = df_map.join(pd.DataFrame(list(ppt_data)).set_index("code")).fillna(0)
    return df_map


def get_sights(region: str, tourism_type: str) -> models.QuerySet:
    """
    Returns region sights according to tourism type
    :param region: str
    :param tourism_type: str
    :return: models.QuerySet
    """
    return (
        Sight.objects.only("id", "address", "group__title", "title", "lon", "lat")
        .filter(
            code=region,
            is_pub=True,
            **dict() if not tourism_type else dict(group__tourism_type=tourism_type)
        )
        .select_related("group")
        .annotate(qty=models.Sum("sight_all_region_popularity__qty"))
    )


def get_cities(code: str) -> models.QuerySet:
    """
    Returns region cities
    :param code: str
    :return: models.QuerySet
    """
    return City.objects.filter(code=code)


def get_sizes(values: list, min_size: int = 10, max_size: int = 30) -> list:
    """
    Returns dots sizes
    :param values: list
    :param min_size: int
    :param max_size: int
    :return: list
    """
    sizes = []
    if len(values):
        if len(values) == 1:
            sizes = [min_size]
        elif len(values) == 2:
            sizes = (
                [min_size, max_size] if values[0] < values[1] else [max_size, min_size]
            )
        elif min(values) == max(values):
            sizes = [min_size] * len(values)
        else:
            step = (max(values) - min(values)) / (max_size - min_size)
            sizes = [min_size + int((v or 0) / step) for v in values]
    return sizes


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
            **dict(tourism_type=tourism_type)
            if tourism_type
            else dict(tourism_type__in=dict(settings.TOURISM_TYPES_OUTSIDE).keys())
        )
        .order_by("-v_type_sex_age")
    )
