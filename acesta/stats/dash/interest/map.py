import logging
import math
import time
from dataclasses import dataclass
from textwrap import wrap

import plotly.graph_objects as go
from dash import dependencies
from dash import html
from dash import no_update
from dash import Patch
from dash.exceptions import PreventUpdate
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma

from acesta.geo.models import City
from acesta.stats.dash.helpers.interest import get_cities
from acesta.stats.dash.helpers.interest import get_city
from acesta.stats.dash.helpers.interest import get_geojson_regions
from acesta.stats.dash.helpers.interest import get_interest_map_context_key
from acesta.stats.dash.helpers.interest import get_map_df
from acesta.stats.dash.helpers.interest import get_sight
from acesta.stats.dash.helpers.interest import get_sights
from acesta.stats.dash.helpers.interest import get_sizes
from acesta.stats.dash.helpers.interest import normalize_interest_context
from acesta.stats.dash.interest.app import interest_app
from acesta.stats.dash.interest.interest import resolve_target_key
from acesta.stats.dash.interest.map_connections import BalloonContent
from acesta.stats.dash.interest.map_connections import build_connection_overlay
from acesta.stats.dash.interest.map_connections import create_point_entity
from acesta.stats.dash.interest.map_connections import create_region_entity
from acesta.stats.dash.interest.map_connections import MapConnection
from acesta.stats.dash.interest.map_connections import parse_entity_key
from acesta.stats.dash.interest.map_connections import SOURCE_CLICK_PREFIX

HOME_REGION_FILL_COLOR = "#4F9286"
COUNTRY_FILL_COLOR = "#eef5f7"
COUNTRY_LINE_COLOR = "#d3dde0"
CITY_POPULARITY_COLORS = {
    "low": "#B8C4C8",
    "medium": "#9CCCC8",
    "high": "#79ADA6",
    "very-high": "#4F9286",
}
POPULARITY_HOVER_COLORS = {
    "low": {"background": "#fefefe", "text": "#5f6871"},
    "medium": {"background": "#76bdb0", "text": "#ffffff"},
    "high": {"background": "#7cbbb0", "text": "#ffffff"},
    "very-high": {"background": "#74b8ac", "text": "#ffffff"},
}
DEFAULT_INTEREST_MAP_HEIGHT = 450
MIN_INTEREST_MAP_HEIGHT = 120
MAX_INTEREST_MAP_HEIGHT = 2000
logger = logging.getLogger(__name__)


def get_interest_map_height(map_viewport: dict) -> int:
    """Return a validated client-measured map height with a safe first-load fallback."""
    if not isinstance(map_viewport, dict):
        return DEFAULT_INTEREST_MAP_HEIGHT

    height = map_viewport.get("height")
    if isinstance(height, bool):
        return DEFAULT_INTEREST_MAP_HEIGHT
    try:
        height = round(float(height))
    except (TypeError, ValueError, OverflowError):
        return DEFAULT_INTEREST_MAP_HEIGHT
    if not MIN_INTEREST_MAP_HEIGHT <= height <= MAX_INTEREST_MAP_HEIGHT:
        return DEFAULT_INTEREST_MAP_HEIGHT
    return height


def get_interest_map_camera(map_camera: dict):
    """Return a validated client camera or ``None`` for unusable data."""
    if not isinstance(map_camera, dict):
        return None

    center = map_camera.get("center")
    if not isinstance(center, dict):
        return None

    values = (center.get("lon"), center.get("lat"), map_camera.get("zoom"))
    if any(isinstance(value, bool) for value in values):
        return None
    try:
        longitude, latitude, zoom = (float(value) for value in values)
    except (TypeError, ValueError, OverflowError):
        return None
    if not all(math.isfinite(value) for value in (longitude, latitude, zoom)):
        return None
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        return None
    if not 0 <= zoom <= 24:
        return None

    return {"lat": latitude, "lon": longitude}, zoom


def get_interest_map_patch(figure: go.Figure) -> Patch:
    """Return only camera and overlay changes for a source selection."""
    figure_patch = Patch()
    figure_patch["layout"]["height"] = figure.layout.height
    figure_patch["layout"]["meta"] = figure.layout.meta
    figure_patch["layout"]["map"]["center"] = figure.layout.map.center.to_plotly_json()
    figure_patch["layout"]["map"]["zoom"] = figure.layout.map.zoom
    figure_patch["layout"]["map"]["layers"] = [
        layer.to_plotly_json() for layer in figure.layout.map.layers
    ]
    return figure_patch


def get_interest_overlay_patch(
    map_height: int,
    camera_intent: dict,
    map_state: dict,
    overlay,
) -> Patch:
    """Build a selection patch directly, without creating a Plotly figure."""
    figure_patch = Patch()
    figure_patch["layout"]["height"] = map_height
    figure_patch["layout"]["meta"] = {
        "acestaInterestCamera": camera_intent,
        "acestaInterestContext": map_state["mapContextKey"],
        "acestaInterestState": map_state,
    }
    figure_patch["layout"]["map"]["center"] = overlay.center
    figure_patch["layout"]["map"]["zoom"] = overlay.zoom
    figure_patch["layout"]["map"]["layers"] = list(overlay.layers)
    return figure_patch


@dataclass(frozen=True)
class PopularityPresentation:
    label: str
    tone: str
    audience_label: str = ""


def get_region_hovertemplate() -> str:
    """Return the shared qualitative hover text used by regional layers."""
    return "<br>".join(
        [
            '<span style="font-size: 11px">Популярность в регионе</span>',
            "<b>%{customdata[0]}</b>",
            "%{customdata[1]}",
            "<extra></extra>",
        ]
    )


def get_popularity_hoverlabel(presentations: list) -> dict:
    """Return per-entity Plotly colors matching the balloon palette."""
    return {
        "bgcolor": [
            POPULARITY_HOVER_COLORS[presentation.tone]["background"]
            for presentation in presentations
        ],
        "bordercolor": "#ffffff",
        "font": {
            "color": [
                POPULARITY_HOVER_COLORS[presentation.tone]["text"]
                for presentation in presentations
            ]
        },
    }


def get_popularity_hover_detail(
    presentation: PopularityPresentation,
    prefix: str = "",
) -> str:
    """Format one qualitative metric with an optional warning line."""
    label = f"{prefix}{presentation.label}"
    if not presentation.audience_label:
        return label
    return f"{label},<br>{presentation.audience_label}"


def get_region_hover_data(regions) -> tuple:
    """Build shared region customdata and matching per-region hover colors."""
    presentations = []
    customdata = []
    for _, row in regions.iterrows():
        presentation = get_popularity_presentation(
            row.get("ppt"),
            row.get("qty"),
        )
        presentations.append(presentation)
        customdata.append(
            [row.get("name", ""), get_popularity_hover_detail(presentation)]
        )
    return customdata, get_popularity_hoverlabel(presentations)


def add_home_region_layer(fig: go.Figure, home_region) -> None:
    """Draw the home region independently from the statistical heatmap."""
    if home_region.empty:
        return

    customdata, hoverlabel = get_region_hover_data(home_region)
    fig.add_trace(
        go.Choroplethmap(
            geojson=home_region.geometry.__geo_interface__,
            locations=home_region.index,
            z=[1] * len(home_region),
            zmin=0,
            zmax=1,
            colorscale=[
                [0, HOME_REGION_FILL_COLOR],
                [1, HOME_REGION_FILL_COLOR],
            ],
            customdata=customdata,
            marker={
                "line": {"color": HOME_REGION_FILL_COLOR, "width": 2},
                "opacity": 1,
            },
            hovertemplate=get_region_hovertemplate(),
            hoverlabel=hoverlabel,
            showscale=False,
            showlegend=False,
        )
    )


def add_country_background_trace(
    fig: go.Figure,
    df_map,
    fill_color: str = COUNTRY_FILL_COLOR,
    opacity: float = 1,
    line_color: str = COUNTRY_LINE_COLOR,
    line_width: float = 1,
) -> None:
    """Keep the static country geometry in figure data, outside later patches."""
    fig.add_trace(
        go.Choroplethmap(
            geojson=df_map.geometry.__geo_interface__,
            locations=df_map.index.tolist(),
            z=[0] * len(df_map),
            zmin=0,
            zmax=1,
            colorscale=[[0, fill_color], [1, fill_color]],
            marker={
                "line": {"color": line_color, "width": line_width},
                "opacity": opacity,
            },
            hoverinfo="skip",
            showscale=False,
            showlegend=False,
        )
    )


def add_home_region_outline_trace(fig: go.Figure, home_region) -> None:
    """Draw the static home boundary without adding it to dynamic map layers."""
    if home_region.empty:
        return
    fig.add_trace(
        go.Choroplethmap(
            geojson=home_region.geometry.__geo_interface__,
            locations=home_region.index,
            z=[0] * len(home_region),
            zmin=0,
            zmax=1,
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            marker={"line": {"color": HOME_REGION_FILL_COLOR, "width": 2}},
            hoverinfo="skip",
            showscale=False,
            showlegend=False,
        )
    )


def get_popularity_presentation(popularity, quantity=None) -> PopularityPresentation:
    """Return the qualitative label, tone, and conditional audience warning."""
    try:
        popularity = float(popularity)
    except (TypeError, ValueError, OverflowError):
        return PopularityPresentation("нет данных", "low")
    if not math.isfinite(popularity):
        return PopularityPresentation("нет данных", "low")

    if popularity > 1000:
        label, tone = "очень высокая", "very-high"
    elif popularity > 500:
        label, tone = "высокая", "high"
    elif popularity > 100:
        label, tone = "средняя", "medium"
    else:
        label, tone = "низкая", "low"

    audience_label = ""
    if popularity > 100:
        try:
            quantity = float(quantity)
        except (TypeError, ValueError, OverflowError):
            quantity = None
        if quantity is not None and math.isfinite(quantity) and quantity < 1000:
            audience_label = "но аудитория ограничена"

    return PopularityPresentation(label, tone, audience_label)


def get_popularity_label(popularity: float) -> str:
    return get_popularity_presentation(popularity).label


def get_popularity_level(popularity: float) -> str:
    return get_popularity_presentation(popularity).tone


def get_audience_label(popularity: float, quantity) -> str:
    return get_popularity_presentation(popularity, quantity).audience_label


def get_popularity_balloon_detail(label: str, audience_label: str):
    """Build one metric block, adding punctuation only with the warning."""
    if not audience_label:
        return label
    return [f"{label},", html.Br(), audience_label]


def format_map_number(value) -> str:
    """Format a finite map metric while keeping missing values empty."""
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        return ""
    if not math.isfinite(value):
        return ""
    return intcomma(round(value))


def get_country_background_layers(
    df_map,
    fill_color: str = COUNTRY_FILL_COLOR,
    opacity: float = 1,
    line_color: str = COUNTRY_LINE_COLOR,
    line_width: float = 1,
) -> list:
    """Return a quiet non-interactive silhouette built from the full GeoJSON."""
    geometry = df_map.geometry.make_valid().union_all()
    source = {
        "type": "Feature",
        "properties": {},
        "geometry": geometry.__geo_interface__,
    }
    return [
        {
            "source": source,
            "sourcetype": "geojson",
            "type": "fill",
            "color": fill_color,
            "opacity": opacity,
            "below": "traces",
        },
        {
            "source": source,
            "sourcetype": "geojson",
            "type": "line",
            "color": line_color,
            "opacity": opacity,
            "line": {"width": line_width},
            "below": "traces",
        },
    ]


def get_home_region_outline_layers(source: dict, home_area: str) -> list:
    """Return the home outline below point traces in point target modes."""
    is_point_mode = home_area in (settings.AREA_CITIES, settings.AREA_SIGHTS)
    position = {"below": "traces"} if is_point_mode else {}
    return [
        {
            "source": source,
            "sourcetype": "geojson",
            "type": "line",
            "color": "#34766A",
            "opacity": 0.04 if is_point_mode else 0.14,
            "line": {"width": 5},
            **position,
        },
        {
            "source": source,
            "sourcetype": "geojson",
            "type": "line",
            "color": "#34766A",
            "opacity": 0.28 if is_point_mode else 0.72,
            "line": {"width": 2},
            **position,
        },
    ]


def get_city_heatmap_items(table_data: list) -> list:
    """Resolve every city table row with one coordinates query."""
    rows_by_id = {
        str(row.get("code")): row
        for row in table_data or []
        if row.get("code") not in (None, "")
    }
    if not rows_by_id:
        return []

    cities_by_id = {
        str(identifier): city
        for identifier, city in City.objects.select_related("code")
        .only("id", "title", "lat", "lon", "code__title")
        .in_bulk(rows_by_id)
        .items()
    }
    return [
        (cities_by_id[identifier], row)
        for identifier, row in rows_by_id.items()
        if identifier in cities_by_id
    ]


def add_city_heatmap_trace(fig: go.Figure, items: list) -> None:
    """Draw clickable cities colored by their popularity level."""
    if not items:
        return

    cities = [city for city, _ in items]
    rows = [row for _, row in items]
    popularity = [get_interest_row_popularity(row) for row in rows]
    presentations = [
        get_popularity_presentation(value, row.get("qty"))
        for value, row in zip(popularity, rows)
    ]
    colors = [CITY_POPULARITY_COLORS[item.tone] for item in presentations]
    quantities = [float(row.get("qty") or 0) for row in rows]

    fig.add_trace(
        go.Scattermap(
            lat=[city.lat for city in cities],
            lon=[city.lon for city in cities],
            text=[row.get("code__title") or city.title for city, row in items],
            marker={
                "color": colors,
                "size": get_sizes(quantities),
                "opacity": 1,
            },
            customdata=[
                [
                    city.code.title,
                    get_popularity_hover_detail(
                        presentation,
                        prefix="популярность ",
                    ),
                ]
                for city, presentation in zip(cities, presentations)
            ],
            ids=[f"{SOURCE_CLICK_PREFIX}cities_{city.pk}" for city in cities],
            mode="markers",
            hovertemplate="<br>".join(
                [
                    '<span style="font-size: 11px">%{customdata[0]}</span>',
                    "<b>%{text}</b>",
                    "%{customdata[1]}",
                    "<extra></extra>",
                ]
            ),
            hoverlabel=get_popularity_hoverlabel(presentations),
            showlegend=False,
        )
    )


def get_selected_interest_row(active_cell: dict, table_data: list):
    """Return the selected source row without depending on the visible row order."""
    if not active_cell or not table_data:
        return None

    row_id = active_cell.get("row_id")
    if row_id not in (None, ""):
        for row in table_data:
            if str(row.get("id", row.get("code"))) == str(row_id):
                return row

    try:
        return table_data[active_cell["row"]]
    except (IndexError, KeyError, TypeError):
        return None


def get_interest_row_popularity(row: dict) -> float:
    """Convert the DataTable percentage fraction back to the stored percentage."""
    try:
        popularity = float(row.get("ppt") or 0) * 100
    except (AttributeError, TypeError, ValueError):
        return 0
    return popularity if math.isfinite(popularity) else 0


def apply_region_table_popularity(df_map, table_data: list):
    """Use the visible region table as the source of truth for map metrics."""
    df_map = df_map.copy()
    df_map["qty"] = 0.0
    df_map["ppt"] = float("nan")
    index_by_code = {str(index): index for index in df_map.index}

    for row in table_data or []:
        if not isinstance(row, dict):
            continue
        index = index_by_code.get(str(row.get("code")))
        if index is None:
            continue
        try:
            quantity = float(row.get("qty") or 0)
        except (TypeError, ValueError, OverflowError):
            quantity = 0
        if not math.isfinite(quantity):
            quantity = 0
        df_map.at[index, "qty"] = quantity
        df_map.at[index, "ppt"] = get_interest_row_popularity(row)

    return df_map


def get_home_region_entity(df_map, current_region):
    region = df_map.loc[df_map.index.astype(str) == str(current_region.code)]
    if region.empty:
        return None, region

    row = region.iloc[0]
    return (
        create_region_entity(
            current_region.code,
            row.get("name", current_region.title),
            row.geometry,
        ),
        region,
    )


def get_target_entity(
    target_key: str,
    home_area: str,
    home_region_entity,
    cities: list,
    sights: list,
):
    """Resolve the persistent target, falling back to the current region."""
    kind, identifier = parse_entity_key(target_key)
    if kind != home_area or identifier in (None, "0"):
        return home_region_entity

    if kind == settings.AREA_CITIES:
        city = next((item for item in cities if str(item.pk) == identifier), None)
        if city is None:
            return home_region_entity
        return create_point_entity(
            settings.AREA_CITIES,
            city.pk,
            city.title,
            city.lon,
            city.lat,
            BalloonContent(title=city.title),
        )

    if kind == settings.AREA_SIGHTS:
        sight = next((item for item in sights if str(item.pk) == identifier), None)
        if sight is None:
            return home_region_entity
        groups = ", ".join(group.title for group in sight.group.all())
        address = (sight.address or "").replace("Россия, ", "").replace("Украина, ", "")
        return create_point_entity(
            settings.AREA_SIGHTS,
            sight.pk,
            sight.title or "",
            sight.lon,
            sight.lat,
            BalloonContent(
                title=sight.title or "",
                eyebrow=groups,
                details=(address,) if address else (),
            ),
        )

    return home_region_entity


def get_source_entity(
    active_cell: dict,
    table_data: list,
    interesant_area: str,
    df_map,
    cities: list,
):
    """Resolve the active table row to a polygon or point source entity."""
    row = get_selected_interest_row(active_cell, table_data)
    if row is None:
        return None

    identifier = row.get("code")
    if identifier in (None, ""):
        return None
    popularity = get_interest_row_popularity(row)
    presentation = get_popularity_presentation(popularity, row.get("qty"))
    label = presentation.label
    audience_label = presentation.audience_label
    details = (get_popularity_balloon_detail(label, audience_label),)
    tone = presentation.tone

    if interesant_area == settings.AREA_REGIONS:
        region = df_map.loc[df_map.index.astype(str) == str(identifier)]
        if region.empty:
            return None
        region_row = region.iloc[0]
        title = row.get("code__title") or region_row.get("name", "")
        return create_region_entity(
            identifier,
            title,
            region_row.geometry,
            BalloonContent(
                title=title,
                eyebrow="Популярность в регионе",
                details=details,
                tone=tone,
            ),
        )

    if interesant_area == settings.AREA_CITIES:
        city = next((item for item in cities if str(item.pk) == str(identifier)), None)
        if city is None:
            city = City.objects.filter(pk=identifier).first()
        if city is None:
            return None
        title = row.get("code__title") or city.title
        return create_point_entity(
            settings.AREA_CITIES,
            city.pk,
            title,
            city.lon,
            city.lat,
            BalloonContent(
                title=title,
                eyebrow="Популярность в городе",
                details=details,
                tone=tone,
            ),
        )

    return None


def get_popularity_heatmap(ppt, scale_ppt=None) -> tuple:
    """Return neutral and increased-interest color values for the heatmap."""
    has_missing = ppt.isna().any()
    if ppt[ppt > 100].empty:
        if not has_missing:
            return ppt * 0, (0, 1), ["#eef5f7", "#eef5f7"]
        color_values = (ppt * 0).where(ppt.notna(), -1)
        return (
            color_values,
            (-1, 0),
            [
                [0, "#ffffff"],
                [0.499, "#ffffff"],
                [0.5, "#eef5f7"],
                [1, "#eef5f7"],
            ],
        )

    scale_ppt = ppt if scale_ppt is None else scale_ppt
    increased_interest = scale_ppt[scale_ppt > 100]
    popularity_cap = (
        max(101, float(increased_interest.quantile(0.95)))
        if not increased_interest.empty
        else 101
    )
    normalized = ((ppt - 100) / (popularity_cap - 100)).clip(0, 1)
    color_values = normalized.where(ppt > 100, 0) + (ppt > 100).astype(int)
    if has_missing:
        return (
            color_values.where(ppt.notna(), -1),
            (-1, 2),
            [
                [0, "#ffffff"],
                [0.332, "#ffffff"],
                [0.333, "#eef5f7"],
                [0.666, "#eef5f7"],
                [0.667, "#B2DFDB"],
                [1, "#90C2BB"],
            ],
        )
    return (
        color_values,
        (0, 2),
        [
            [0, "#eef5f7"],
            [0.499, "#eef5f7"],
            [0.5, "#B2DFDB"],
            [1, "#90C2BB"],
        ],
    )


def get_home_region_card(region) -> list:
    """Build the current-region card shown over every interest map tab."""
    potential_text = (
        "Лидер по потенциалу"
        if region.rank == 4
        else f"{region.get_rank_display()} потенциал"
    )
    return [
        html.Div(
            [
                html.Img(
                    src=f"/static/img/blazon/{region.code}.svg",
                    className="region-current-card__blazon",
                    alt="",
                ),
                html.Div(
                    [
                        html.Div(
                            "Анализируем регион",
                            className="region-current-card__eyebrow",
                        ),
                        html.H4(
                            region.title,
                            className="region-current-card__title",
                        ),
                        html.Div(
                            (
                                f"{region.get_federal_district_display()} "
                                "федеральный округ"
                            ),
                            className="region-current-card__district",
                        ),
                    ],
                    className="region-current-card__heading",
                ),
            ],
            className="region-current-card__header",
        ),
        html.Div(
            [
                html.Span(
                    className="region-current-card__potential-icon",
                    **{"data-rank": str(region.rank), "aria-hidden": "true"},
                ),
                html.Span(
                    potential_text,
                    className="region-current-card__potential-text",
                ),
            ],
            className=(
                "region-current-card__potential metric metric-rank "
                f"rank-{region.rank}"
            ),
        ),
    ]


def get_empty_sights_balloon():
    """Return the centered neutral state used when a region has no sights."""
    return html.Div(
        html.H4("Нет данных", className="interest-map-balloon__title"),
        className=(
            "interest-map-balloon interest-map-balloon--popularity-low "
            "interest-map-balloon--empty"
        ),
        role="status",
    )


def get_fast_interest_map_patch(
    current_region,
    home_area: str,
    interesant_area: str,
    tourism_type: str,
    target_key: str,
    map_context_key: str,
    map_viewport: dict,
    map_camera: dict,
    table_data: list,
    active_cell: dict,
):
    """Build only selection-dependent layers for an existing map baseline."""
    selected_row = get_selected_interest_row(active_cell, table_data)
    selected_code = selected_row.get("code") if selected_row else None
    region_codes = {current_region.code}
    if interesant_area == settings.AREA_REGIONS and selected_code not in (None, ""):
        region_codes.add(selected_code)

    region_frame = get_geojson_regions(region_codes)
    region_frame["qty"] = 0
    region_frame["ppt"] = float("nan")
    home_region_entity, _ = get_home_region_entity(region_frame, current_region)

    target_kind, target_identifier = parse_entity_key(target_key)
    cities = []
    sights = []
    if (
        home_area == settings.AREA_CITIES
        and target_kind == settings.AREA_CITIES
        and target_identifier not in (None, "0")
    ):
        target_city = get_city(target_identifier, current_region.code)
        if target_city is not None:
            cities.append(target_city)
    elif (
        home_area == settings.AREA_SIGHTS
        and target_kind == settings.AREA_SIGHTS
        and target_identifier not in (None, "0")
    ):
        target_sight = get_sight(
            current_region.code,
            target_identifier,
            tourism_type,
        )
        if target_sight is not None:
            sights.append(target_sight)

    if interesant_area == settings.AREA_CITIES and selected_code not in (None, ""):
        if not any(str(city.pk) == str(selected_code) for city in cities):
            source_city = get_city(selected_code)
            if source_city is not None:
                cities.append(source_city)

    target = get_target_entity(
        target_key,
        home_area,
        home_region_entity,
        cities,
        sights,
    )
    if (
        home_area in (settings.AREA_CITIES, settings.AREA_SIGHTS)
        and target_kind == home_area
        and target_identifier == "0"
    ):
        target = None
    if target is not None and home_area in (
        settings.AREA_CITIES,
        settings.AREA_SIGHTS,
    ):
        target = target.with_balloon(None)

    source = get_source_entity(
        active_cell,
        table_data,
        interesant_area,
        region_frame,
        cities,
    )
    connections = []
    if source is not None and target is not None:
        if source.key == target.key and target.kind == settings.AREA_REGIONS:
            content = source.balloon
            source = source.with_balloon(
                BalloonContent(
                    title="среди жителей",
                    eyebrow="Популярность домашнего региона",
                    details=content.details,
                    tone=content.tone,
                )
            )
        connections.append(MapConnection(source=source, target=target))

    default_center = {
        "lat": current_region.center_lat,
        "lon": current_region.center_lon,
    }
    default_zoom = (
        current_region.zoom_regions
        if home_area == settings.AREA_REGIONS
        else current_region.zoom_cities
    )
    persistent_entities = []
    if target is not None and target.kind != settings.AREA_REGIONS:
        persistent_entities.append(target)
        saved_camera = get_interest_map_camera(map_camera)
        preserve_camera = (
            home_area == settings.AREA_SIGHTS
            and source is None
            and target.kind == settings.AREA_SIGHTS
            and saved_camera is not None
        )
        if preserve_camera:
            default_center, default_zoom = saved_camera
        else:
            default_center = {"lat": target.anchor[1], "lon": target.anchor[0]}

    map_height = get_interest_map_height(map_viewport)
    overlay = build_connection_overlay(
        connections,
        map_viewport,
        map_height,
        default_center,
        default_zoom,
        persistent_entities,
    )
    camera_key = "|".join(
        str(value or "")
        for value in (
            home_area,
            interesant_area,
            tourism_type,
            source.key if source is not None else "",
            target.key if target is not None else "",
            (map_viewport or {}).get("width"),
            (map_viewport or {}).get("height"),
            (map_viewport or {}).get("topInset"),
        )
    )
    camera_intent = {
        "key": camera_key,
        "center": overlay.center,
        "zoom": overlay.zoom,
    }
    map_state = {
        "ready": True,
        "mapContextKey": map_context_key,
        "sourceRowId": active_cell.get("row_id") if active_cell else None,
        "targetKey": target_key,
    }
    return (
        get_interest_overlay_patch(
            map_height,
            camera_intent,
            map_state,
            overlay,
        ),
        list(overlay.balloons),
    )


@interest_app.callback(
    dependencies.Output("map", "figure"),
    dependencies.Output("region-current-card-content", "children"),
    dependencies.Output("interest-map-balloons", "children"),
    dependencies.Input("interest-table-state", "data"),
    dependencies.Input("table-interesants", "active_cell"),
    dependencies.State("tourism-type", "value"),
    dependencies.State("home-area", "value"),
    dependencies.State("tabs-interesants", "value"),
    dependencies.State("home-area-key", "data"),
    dependencies.State("interest-map-viewport", "data"),
    dependencies.State("table-interesants", "data"),
    dependencies.State("interest-map-camera", "data"),
    dependencies.State("interest-session-hydrated", "data"),
    dependencies.State("interest-map-state", "data"),
)
def update_map(
    table_state: dict,
    active_cell: dict,
    tourism_type: str,
    home_area: str,
    interesant_area: str,
    target_key: str,
    map_viewport: dict,
    table_data: list,
    map_camera: dict = None,
    hydrated: bool = False,
    current_map_state: dict = None,
    *args,
    **kwargs,
) -> tuple:
    """
    Updates the map
    :param tourism_type: str
    :param home_area: str
    :param interesant_area: str
    :param active_cell: dict
    :param map_viewport: dict
    :param table_data: list
    :param map_camera: dict
    :param args: list
    :param kwargs: dict
    :return: dcc.Graph
    """
    started_at = time.perf_counter()
    user = kwargs.get("user")
    if not table_state:
        raise PreventUpdate

    home_area, interesant_area, tourism_type = normalize_interest_context(
        user, home_area, interesant_area, tourism_type
    )
    current_region = user.current_region
    target_key = resolve_target_key(
        user,
        home_area,
        tourism_type,
        target_key,
    )
    map_context_key = get_interest_map_context_key(
        current_region.code,
        home_area,
        interesant_area,
        tourism_type,
        target_key,
    )
    expected_table_context = {
        "homeArea": home_area,
        "interesantArea": interesant_area,
        "tourismType": tourism_type,
        "targetKey": target_key,
        "mapContextKey": map_context_key,
    }
    if any(
        table_state.get(key) != value for key, value in expected_table_context.items()
    ):
        raise PreventUpdate

    baseline_matches = bool(
        current_map_state
        and current_map_state.get("ready") is True
        and current_map_state.get("mapContextKey") == map_context_key
    )
    if hydrated and baseline_matches:
        patch, balloons = get_fast_interest_map_patch(
            current_region,
            home_area,
            interesant_area,
            tourism_type,
            target_key,
            map_context_key,
            map_viewport,
            map_camera,
            table_data,
            active_cell,
        )
        logger.info(
            "interest_map branch=patch context=%s elapsed_ms=%.1f",
            map_context_key,
            (time.perf_counter() - started_at) * 1000,
        )
        return patch, no_update, balloons

    city_source_mode = interesant_area == settings.AREA_CITIES
    city_source_region_mode = home_area == settings.AREA_REGIONS and city_source_mode
    city_source_point_mode = (
        home_area in (settings.AREA_CITIES, settings.AREA_SIGHTS) and city_source_mode
    )
    base_color = "heatmap_ppt" if home_area == settings.AREA_REGIONS else None
    df_map = get_map_df(tourism_type, current_region)
    if interesant_area == settings.AREA_REGIONS:
        df_map = apply_region_table_popularity(df_map, table_data)
    df_map["qty_str"] = df_map["qty"].apply(format_map_number)
    df_map["ppt_str"] = df_map["ppt"].apply(format_map_number)
    home_region_mask = df_map.index.astype(str) == str(current_region.code)
    external_region_ppt = df_map.loc[~home_region_mask, "ppt"]
    (
        external_heatmap_ppt,
        popularity_range,
        popularity_scale,
    ) = get_popularity_heatmap(external_region_ppt)
    df_map["heatmap_ppt"] = float("nan")
    df_map.loc[~home_region_mask, "heatmap_ppt"] = external_heatmap_ppt

    map_height = get_interest_map_height(map_viewport)
    default_center = {
        "lat": current_region.center_lat,
        "lon": current_region.center_lon,
    }
    default_zoom = (
        current_region.zoom_regions
        if home_area == settings.AREA_REGIONS
        else current_region.zoom_cities
    )
    cities = []
    sights = []
    city_heatmap_items = []
    if home_area == settings.AREA_CITIES and user.is_extended:
        cities = list(get_cities(current_region.code))
    elif home_area == settings.AREA_SIGHTS and user.is_extended:
        sights = list(get_sights(current_region.code, tourism_type))
    if city_source_mode and user.is_extended:
        city_heatmap_items = get_city_heatmap_items(table_data)

    target_kind, target_identifier = parse_entity_key(target_key)
    home_region_entity, home_region = get_home_region_entity(df_map, current_region)
    target = get_target_entity(
        target_key,
        home_area,
        home_region_entity,
        cities,
        sights,
    )
    if (
        home_area in (settings.AREA_CITIES, settings.AREA_SIGHTS)
        and target_kind == home_area
        and target_identifier == "0"
    ):
        target = None
    if target is not None and home_area in (
        settings.AREA_CITIES,
        settings.AREA_SIGHTS,
    ):
        target = target.with_balloon(None)
    source = get_source_entity(
        active_cell,
        table_data,
        interesant_area,
        df_map,
        [city for city, _ in city_heatmap_items] if city_source_mode else cities,
    )

    connections = []
    if source is not None and target is not None:
        if source.key == target.key and target.kind == settings.AREA_REGIONS:
            content = source.balloon
            source = source.with_balloon(
                BalloonContent(
                    title="среди жителей",
                    eyebrow="Популярность домашнего региона",
                    details=content.details,
                    tone=content.tone,
                )
            )
        connections.append(MapConnection(source=source, target=target))

    persistent_entities = []
    if target is not None and target.kind != settings.AREA_REGIONS:
        persistent_entities.append(target)
        saved_camera = get_interest_map_camera(map_camera)
        preserve_camera = (
            home_area == settings.AREA_SIGHTS
            and source is None
            and target.kind == settings.AREA_SIGHTS
            and saved_camera is not None
        )
        if preserve_camera:
            default_center, default_zoom = saved_camera
        else:
            default_center = {"lat": target.anchor[1], "lon": target.anchor[0]}

    overlay = build_connection_overlay(
        connections,
        map_viewport,
        map_height,
        default_center,
        default_zoom,
        persistent_entities,
    )
    camera_key = "|".join(
        str(value or "")
        for value in (
            home_area,
            interesant_area,
            tourism_type,
            source.key if source is not None else "",
            target.key if target is not None else "",
            (map_viewport or {}).get("width"),
            (map_viewport or {}).get("height"),
            (map_viewport or {}).get("topInset"),
        )
    )
    camera_intent = {
        "key": camera_key,
        "center": overlay.center,
        "zoom": overlay.zoom,
    }
    source_row_id = active_cell.get("row_id") if active_cell else None
    next_map_state = {
        "ready": True,
        "mapContextKey": map_context_key,
        "sourceRowId": source_row_id,
        "targetKey": target_key,
    }

    def get_map_figure():
        map_layers = []
        if city_source_region_mode:
            fig = go.Figure()
            add_country_background_trace(fig, df_map)
        elif city_source_point_mode:
            fig = go.Figure()
            add_country_background_trace(
                fig,
                df_map,
                fill_color="#dbfffa",
                opacity=0.45,
                line_color="#000000",
                line_width=0.5,
            )
        else:
            region_customdata, region_hoverlabel = get_region_hover_data(df_map)
            region_mode = home_area == settings.AREA_REGIONS
            z_values = df_map[base_color].tolist() if region_mode else [0] * len(df_map)
            colorscale = (
                popularity_scale if region_mode else [[0, "#dbfffa"], [1, "#dbfffa"]]
            )
            zmin, zmax = popularity_range if region_mode else (0, 1)
            fig = go.Figure(
                go.Choroplethmap(
                    geojson=df_map.geometry.__geo_interface__,
                    locations=df_map.index.tolist(),
                    z=z_values,
                    zmin=zmin,
                    zmax=zmax,
                    colorscale=colorscale,
                    customdata=region_customdata,
                    marker={
                        "line": {
                            "color": "#d3dde0" if region_mode else "#000000",
                            "width": 0.5,
                        },
                        "opacity": 1 if region_mode else 0.45,
                    },
                    hovertemplate=get_region_hovertemplate(),
                    hoverlabel=region_hoverlabel,
                    showscale=False,
                    showlegend=False,
                )
            )
            fig.update_layout(
                map={
                    "style": "white-bg" if region_mode else "open-street-map",
                    "zoom": overlay.zoom,
                    "center": overlay.center,
                },
                height=map_height,
            )
            fig.update_traces(
                marker=dict(
                    line=dict(
                        color="#d3dde0" if region_mode else "#000000",
                        width=0.5,
                    ),
                ),
                hovertemplate=get_region_hovertemplate(),
                customdata=region_customdata,
                hoverlabel=region_hoverlabel,
            )
            if region_mode:
                add_home_region_layer(fig, home_region)

        if not home_region.empty:
            if city_source_region_mode:
                add_home_region_layer(fig, home_region)
            if city_source_region_mode or home_area != settings.AREA_REGIONS:
                add_home_region_outline_trace(fig, home_region)

        map_layers.extend(overlay.layers)

        if city_source_mode:
            add_city_heatmap_trace(fig, city_heatmap_items)
        if home_area == settings.AREA_CITIES and user.is_extended:
            fig.add_trace(
                go.Scattermap(
                    lat=[city.lat for city in cities],
                    lon=[city.lon for city in cities],
                    text=[city.title for city in cities],
                    marker={
                        "color": "#85D1F2",
                        "size": get_sizes([city.population for city in cities]),
                        "opacity": 1,
                    },
                    ids=[f"cities_{city.id}" for city in cities],
                    mode="markers",
                    hovertemplate="<br>".join(
                        ["<b>%{text}</b><br>", "<extra></extra>"]
                    ),
                    showlegend=False,
                )
            )
        elif home_area == settings.AREA_SIGHTS and user.is_extended:
            lat = []
            lon = []
            qty = []
            ids = []
            title = []
            extra = []
            color = []
            for sight in sights:
                groups = list(sight.group.all())
                address = (
                    (sight.address or "")
                    .replace("Россия, ", "")
                    .replace("Украина, ", "")
                )
                lat.append(sight.lat)
                lon.append(sight.lon)
                qty.append(sight.qty or 0)
                color.append(
                    settings.SIGHT_GROUPS_PALETTE.get(groups[0].pk)
                    if groups
                    else "#F3B869"
                )
                ids.append(f"sights_{sight.id}")
                title.append(sight.title)
                extra.append(
                    [
                        ",".join(group.title for group in groups),
                        "<br>".join(wrap(address, 45)),
                    ]
                )

            fig.add_trace(
                go.Scattermap(
                    lat=lat,
                    lon=lon,
                    text=title,
                    marker={"color": color, "size": get_sizes(qty), "opacity": 1},
                    customdata=extra,
                    ids=ids,
                    mode="markers",
                    hovertemplate="<br>".join(
                        [
                            "%{customdata[0]}",
                            "<b>%{text}</b><br>",
                            "%{customdata[1]}",
                            "<extra></extra>",
                        ]
                    ),
                    showlegend=False,
                )
            )
        map_layout = {"layers": map_layers}
        if city_source_region_mode:
            map_layout.update(
                {
                    "style": "white-bg",
                    "zoom": overlay.zoom,
                    "center": overlay.center,
                }
            )
        elif city_source_point_mode:
            map_layout.update(
                {
                    "style": "open-street-map",
                    "zoom": overlay.zoom,
                    "center": overlay.center,
                }
            )
        fig.update_layout(
            height=map_height,
            meta={
                "acestaInterestCamera": camera_intent,
                "acestaInterestContext": map_context_key,
                "acestaInterestState": next_map_state,
            },
            hoverlabel={
                "font": {"color": "#FFFFFF"},
                "bordercolor": "#FFFFFF",
            },
            map=map_layout,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            showlegend=False,
        )
        return fig

    balloons = list(overlay.balloons)
    if home_area == settings.AREA_SIGHTS and not sights:
        balloons.append(get_empty_sights_balloon())

    figure = get_map_figure()
    if not hydrated:
        full_reason = "hydrating"
    elif not current_map_state or current_map_state.get("ready") is not True:
        full_reason = "baseline_not_ready"
    else:
        full_reason = "context_changed"
    logger.info(
        "interest_map branch=full reason=%s context=%s elapsed_ms=%.1f",
        full_reason,
        map_context_key,
        (time.perf_counter() - started_at) * 1000,
    )
    return figure, get_home_region_card(current_region), balloons
