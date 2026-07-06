from functools import lru_cache

import geopandas as gpd
import pandas as pd
from django.apps import apps
from django.conf import settings
from django.db import models
from django.utils.timesince import timesince

from acesta.base.utils import timesince_accusatifier as accusatifier
from acesta.base.utils import timesince_cutter as cutter
from acesta.geo.models import City
from acesta.geo.models import Sight
from acesta.stats.helpers.update_dates import get_auditory_update_date
from acesta.stats.helpers.update_dates import get_avg_bill_update_date
from acesta.stats.helpers.update_dates import get_avg_salary_update_date
from acesta.stats.helpers.update_dates import get_rating_update_date


HISTORY_ENTITY_TYPES = {
    "RegionRegionPopularity": "region_region",
    "RegionCityPopularity": "region_city",
    "CityRegionPopularity": "city_region",
    "CityCityPopularity": "city_city",
    "AllRegionPopularity": "sight_region",
    "AllCityPopularity": "sight_city",
}
INTEREST_SESSION_VERSION = 2
LEGACY_INTEREST_SESSION_VERSION = 1
DEFAULT_INTEREST_SORT = {"column_id": "qty_display", "direction": "desc"}
INTEREST_SORT_ALIASES = {
    "ppt": "ppt_display",
    "qty": "qty_display",
}
INTEREST_SORT_COLUMNS = {
    "code__title",
    "ppt_display",
    "qty_display",
}
INTEREST_NUMERIC_SORT_COLUMNS = {"ppt_display", "qty_display"}


def normalize_interest_context(
    user,
    home_area: str,
    interesant_area: str,
    tourism_type: str,
) -> tuple[str, str, str]:
    """Validate client-restored filters against the user's current access."""
    tourism_type = tourism_type or ""
    known_tourism_types = dict(settings.TOURISM_TYPES_OUTSIDE)
    if tourism_type not in known_tourism_types:
        tourism_type = ""

    if not user.is_extended:
        return settings.AREA_REGIONS, settings.AREA_REGIONS, tourism_type

    allowed_home_areas = {settings.AREA_REGIONS, settings.AREA_SIGHTS}
    if (
        getattr(user.current_region, "region_type", None)
        != settings.REGION_TYPE_FEDERAL_CITY
    ):
        allowed_home_areas.add(settings.AREA_CITIES)
    if home_area not in allowed_home_areas:
        home_area = settings.AREA_REGIONS

    if interesant_area not in {settings.AREA_REGIONS, settings.AREA_CITIES}:
        interesant_area = settings.AREA_REGIONS

    if home_area != settings.AREA_REGIONS and getattr(
        user, "is_set_tourism_types", False
    ):
        tourism_type = user.get_current_tourism_type(tourism_type)

    return home_area, interesant_area, tourism_type


def normalize_interest_sort(sort_by: list) -> list:
    """Return a safe DataTable sort definition restored from the browser."""
    if sort_by == []:
        return []
    if not isinstance(sort_by, list):
        return [DEFAULT_INTEREST_SORT.copy()]

    normalized = []
    seen_columns = set()
    for item in sort_by:
        if not isinstance(item, dict):
            continue
        column_id = INTEREST_SORT_ALIASES.get(
            item.get("column_id"), item.get("column_id")
        )
        direction = item.get("direction")
        if (
            column_id not in INTEREST_SORT_COLUMNS
            or direction not in {"asc", "desc"}
            or column_id in seen_columns
        ):
            continue
        normalized.append({"column_id": column_id, "direction": direction})
        seen_columns.add(column_id)
    return normalized or [DEFAULT_INTEREST_SORT.copy()]


def get_interest_map_context_key(
    region_code,
    home_area: str,
    interesant_area: str,
    tourism_type: str,
    target_key: str,
) -> str:
    """Identify the table-backed static map context used by a full figure."""
    return "|".join(
        str(value or "")
        for value in (
            region_code,
            home_area,
            interesant_area,
            tourism_type,
            target_key,
        )
    )


def migrate_interest_sort(sort_by: list, session_version: int) -> list:
    """Convert legacy inverted numeric sorting to standard Dash semantics."""
    normalized = normalize_interest_sort(sort_by)
    if session_version != LEGACY_INTEREST_SESSION_VERSION:
        return normalized

    legacy_item = sort_by[0] if isinstance(sort_by, list) and sort_by else None
    if not isinstance(legacy_item, dict):
        return [DEFAULT_INTEREST_SORT.copy()]
    legacy_column = INTEREST_SORT_ALIASES.get(
        legacy_item.get("column_id"), legacy_item.get("column_id")
    )
    if legacy_column not in INTEREST_SORT_COLUMNS or legacy_item.get(
        "direction"
    ) not in {"asc", "desc"}:
        return [DEFAULT_INTEREST_SORT.copy()]
    if normalized[0]["column_id"] in INTEREST_NUMERIC_SORT_COLUMNS:
        normalized[0]["direction"] = (
            "desc" if normalized[0]["direction"] == "asc" else "asc"
        )
    return normalized


def get_restorable_interest_state(state: dict, user) -> dict:
    """Normalize session state and reject data saved for another region."""
    defaults = {
        "version": INTEREST_SESSION_VERSION,
        "regionCode": str(user.current_region.code),
        "homeArea": settings.AREA_REGIONS,
        "interesantArea": settings.AREA_REGIONS,
        "tourismType": "",
        "sortBy": [DEFAULT_INTEREST_SORT.copy()],
        "sourceRowId": None,
        "targetKey": f"{settings.AREA_REGIONS}_0",
    }
    if (
        not isinstance(state, dict)
        or state.get("version")
        not in {LEGACY_INTEREST_SESSION_VERSION, INTEREST_SESSION_VERSION}
        or str(state.get("regionCode")) != str(user.current_region.code)
    ):
        return defaults

    home_area, interesant_area, tourism_type = normalize_interest_context(
        user,
        state.get("homeArea"),
        state.get("interesantArea"),
        state.get("tourismType"),
    )
    normalized = {
        **defaults,
        "homeArea": home_area,
        "interesantArea": interesant_area,
        "tourismType": tourism_type,
        "sortBy": migrate_interest_sort(state.get("sortBy"), state.get("version")),
    }
    if (
        home_area == state.get("homeArea")
        and interesant_area == state.get("interesantArea")
        and tourism_type == (state.get("tourismType") or "")
    ):
        normalized["sourceRowId"] = state.get("sourceRowId")
        normalized["targetKey"] = state.get("targetKey") or defaults["targetKey"]
    return normalized


def get_callback_triggered_id(callback_context) -> str | None:
    """Return the component id that triggered a django-plotly-dash callback."""
    triggered = getattr(callback_context, "triggered", None)
    if not triggered:
        return None

    try:
        prop_id = triggered[0].get("prop_id", "")
    except (AttributeError, IndexError, TypeError):
        return None

    component_id, separator, _ = prop_id.rpartition(".")
    return component_id if separator else None


def generate_update_tooltip_content():
    return f"""
        Данные об интересе обновлены <span class='text-nowrap'>
        {cutter(accusatifier(timesince(get_rating_update_date())))} назад
        </span><br><br>
        Данные о целевых группах обновлены <span class='text-nowrap'>
        {cutter(accusatifier(timesince(get_auditory_update_date())))} назад
        </span><br><br>
        Данные о средней зарплате обновлены <span class='text-nowrap'>
        {cutter(accusatifier(timesince(get_avg_salary_update_date())))} назад
        </span><br><br>
        Данные о среднем чеке обновлены <span class='text-nowrap'>
        {cutter(accusatifier(timesince(get_avg_bill_update_date())))} назад
        </span>
    """


@lru_cache(maxsize=1)
def _get_geojson_cached() -> gpd.GeoDataFrame:
    geojson = gpd.read_file(settings.GEOJSON)
    return geojson.set_index("code")


def get_geojson() -> gpd.GeoDataFrame:
    """
    Returns Russia regions geodata
    :return: gpd.GeoDataFrame
    """
    return _get_geojson_cached().copy()


def get_geojson_regions(codes) -> gpd.GeoDataFrame:
    """Return only requested regions without copying the full country frame."""
    normalized_codes = {str(code) for code in codes if code not in (None, "")}
    geojson = _get_geojson_cached()
    mask = geojson.index.astype(str).isin(normalized_codes)
    return geojson.loc[mask].copy()


def get_ppt_df(ppt_data, sort_by: list) -> pd.DataFrame:
    """
    Returns popularity as a DataFrame
    :param ppt_data
    :param sort_by
    :return: pd.DataFrame
    """
    columns = (
        "pk",
        "code__title",
        "code",
        "qty",
        "ppt",
        "modified",
        "history",
    )
    if isinstance(ppt_data, dict) and "rows" in ppt_data:
        model = apps.get_model(ppt_data["model_label"])
        rows = ppt_data["rows"]
    else:
        model = ppt_data.model
        rows = list(ppt_data.values(*columns))
    df = pd.DataFrame(rows, columns=columns)
    if not len(df):
        df = pd.DataFrame(
            [[None, "Запрашивают редко", "", "", "", None, []]], columns=columns
        )
    else:

        def get_previous_item(row):
            popularity = model(modified=row["modified"], history=row["history"])
            return popularity.previous_history_item

        def get_trend(current, previous):
            if previous is None or current == previous:
                return (
                    '<span class="interest-trend-slot place_change '
                    'place_change_neural">-</span>'
                )
            if current > previous:
                return '<span class="interest-trend-slot place_change">' "&uarr;</span>"
            return (
                '<span class="interest-trend-slot place_change '
                'place_change_negative">&darr;</span>'
            )

        def format_number(value):
            return f"{round(value):,}".replace(",", " ")

        previous_items = df.apply(get_previous_item, axis=1)
        df["qty_display"] = [
            f'{format_number(current)}{get_trend(current, previous.get("qty"))}'
            for current, previous in zip(df["qty"], previous_items)
        ]
        df["ppt_display"] = [
            f'{format_number(current)}%{get_trend(current, previous.get("mean"))}'
            for current, previous in zip(df["ppt"], previous_items)
        ]
        df["ppt"] = df["ppt"] / 100

        entity_type = HISTORY_ENTITY_TYPES.get(model.__name__, "")
        sprite_url = f"{settings.STATIC_URL}img/sprite.svg#history"
        df["history_action"] = [
            (
                (
                    '<button type="button" class="history-action" '
                    'title="Показать историю" aria-label="Показать историю" '
                    'data-bs-toggle="tooltip" '
                    'data-history-domain="popularity" '
                    f'data-history-entity-type="{entity_type}" '
                    f'data-history-entity-id="{pk}">'
                    f'<svg aria-hidden="true"><use href="{sprite_url}"></use></svg>'
                    "</button>"
                )
                if pk and entity_type
                else ""
            )
            for pk in df["pk"]
        ]

    if not df.iloc[0].get("qty_display"):
        empty_slot = '<span class="interest-trend-slot">&nbsp;</span>'
        df["qty_display"] = empty_slot
        df["ppt_display"] = empty_slot
        df["history_action"] = ""

    df = df.drop(columns=["modified", "history"])

    # Dash DataTable uses this special field as a stable row identifier. It
    # keeps the selected region attached to its code when the table is sorted.
    df["id"] = df["code"]

    if sort_by:
        normalized_sort = normalize_interest_sort(sort_by)
        sort_columns = [
            {
                "qty_display": "qty",
                "ppt_display": "ppt",
            }.get(item["column_id"], item["column_id"])
            for item in normalized_sort
        ]
        ascending = [item["direction"] == "asc" for item in normalized_sort]
        if "code" not in sort_columns:
            sort_columns.append("code")
            ascending.append(True)
        df = df.sort_values(sort_columns, ascending=ascending)
    else:
        df = df.sort_values(["code__title", "code"], ascending=[True, True])
    return df


def get_map_df(tourism_type: str, home_code: str) -> pd.DataFrame:
    """
    Returns map data
    :param tourism_type:
    :param home_code: str
    :return: pd.DataFrame
    """
    # Metrics are already present in the table callback payload. Keeping only
    # the static region frame here avoids a duplicate popularity query for
    # every map redraw.
    df_map = get_geojson()
    df_map["qty"] = 0
    df_map["ppt"] = float("nan")
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
            **dict() if not tourism_type else dict(group__tourism_type=tourism_type),
        )
        .annotate(qty=models.Sum("sight_all_region_popularity__qty"))
        .prefetch_related("group")
    )


def get_cities(code: str) -> models.QuerySet:
    """
    Returns region cities
    :param code: str
    :return: models.QuerySet
    """
    return City.objects.filter(code=code)


def get_city(city_id, code: str = None):
    """Return one city, optionally constrained to the current region."""
    filters = {"pk": city_id}
    if code is not None:
        filters["code"] = code
    return City.objects.only("id", "title", "lat", "lon").filter(**filters).first()


def get_sight(region: str, sight_id, tourism_type: str):
    """Return one published sight valid for the current map context."""
    filters = {
        "code": region,
        "pk": sight_id,
        "is_pub": True,
    }
    if tourism_type:
        filters["group__tourism_type"] = tourism_type
    return (
        Sight.objects.only("id", "address", "group", "title", "lon", "lat")
        .filter(**filters)
        .prefetch_related("group")
        .first()
    )


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
