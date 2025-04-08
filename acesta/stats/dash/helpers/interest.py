import geopandas as gpd
import pandas as pd
from django.conf import settings
from django.db import models

from acesta.geo.models import City
from acesta.geo.models import Sight
from acesta.stats.models import RegionRegionPopularity


def get_geojson() -> gpd.GeoDataFrame:
    """
    Returns Russia regions geodata
    :return: gpd.GeoDataFrame
    """
    geojson = gpd.read_file(settings.GEOJSON)
    geojson = geojson.set_index("code")
    return geojson


def get_ppt_df(ppt_data, sort_by: list) -> pd.DataFrame:
    """
    Returns popularity as a DataFrame
    :param ppt_data
    :param sort_by
    :return: pd.DataFrame
    """
    columns = (
        "code__title",
        "code",
        "qty",
        "ppt",
    )
    df = pd.DataFrame.from_records(ppt_data.values(*columns))
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
            **(
                dict(tourism_type=tourism_type)
                if tourism_type
                else dict(tourism_type__isnull=True)
            )
        )
        .values("code")
        .annotate(qty=models.Sum("qty"), ppt=models.Avg("popularity_mean"))
    )
    try:
        df_map = df_map.join(pd.DataFrame(list(ppt_data)).set_index("code")).fillna(0)
    except KeyError:
        df_map["qty"] = 0
        df_map["ppt"] = 0
    return df_map


def get_sights(region: str, tourism_type: str) -> models.QuerySet:
    """
    Returns region sights according to tourism type
    :param region: str
    :param tourism_type: str
    :return: models.QuerySet
    """
    return (
        Sight.objects.only("id", "address", "group", "title", "lon", "lat")
        .filter(
            code=region,
            is_pub=True,
            **dict() if not tourism_type else dict(group__tourism_type=tourism_type)
        )
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
