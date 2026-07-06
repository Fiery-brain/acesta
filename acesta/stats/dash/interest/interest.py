import pandas as pd
from dash import dependencies
from dash.exceptions import PreventUpdate
from django.conf import settings
from django.db import models

from acesta.base.decorators import to_cache
from acesta.geo.models import City
from acesta.geo.models import Sight
from acesta.stats.dash.helpers.interest import generate_update_tooltip_content
from acesta.stats.dash.helpers.interest import get_callback_triggered_id
from acesta.stats.dash.helpers.interest import get_interest_map_context_key
from acesta.stats.dash.helpers.interest import get_ppt_df
from acesta.stats.dash.helpers.interest import get_restorable_interest_state
from acesta.stats.dash.helpers.interest import INTEREST_SESSION_VERSION
from acesta.stats.dash.helpers.interest import normalize_interest_context
from acesta.stats.dash.helpers.interest import normalize_interest_sort
from acesta.stats.dash.interest.app import interest_app
from acesta.stats.dash.interest.map_connections import get_click_entity_key
from acesta.stats.dash.interest.map_connections import get_source_click_entity_key
from acesta.stats.dash.interest.map_connections import parse_entity_key
from acesta.stats.helpers.interest import get_interest_table_rows
from acesta.stats.models import AllRegionPopularity


def is_valid_target(
    region_code: str,
    home_area: str,
    target_id: int,
    tourism_type: str,
) -> bool:
    """Keep a persisted point target only while it belongs to the visible map."""
    if home_area == settings.AREA_CITIES:
        return City.objects.filter(pk=target_id, code_id=region_code).exists()
    if home_area == settings.AREA_SIGHTS:
        filters = {
            "pk": target_id,
            "code_id": region_code,
            "is_pub": True,
        }
        if tourism_type:
            filters["group__tourism_type"] = tourism_type
        return Sight.objects.filter(**filters).exists()
    return False


def get_default_target_key(user, home_area: str, tourism_type: str) -> str:
    """Return the deterministic target used when no point has been selected."""
    if home_area == settings.AREA_REGIONS:
        return f"{settings.AREA_REGIONS}_0"

    if home_area == settings.AREA_CITIES:
        capital = (
            City.objects.filter(
                code_id=user.current_region.code,
                is_capital=True,
            )
            .order_by("pk")
            .first()
        )
        return f"{home_area}_{capital.pk}" if capital else f"{home_area}_0"

    target = get_default_sight_target(user.current_region.code, tourism_type)
    return f"{home_area}_{target['id']}" if target["id"] else f"{home_area}_0"


@to_cache(
    "interest_default_sight_v3_{region_code}_{tourism_type}",
    60 * 60 * 24 * 7,
)
def get_default_sight_target(region_code: str, tourism_type: str) -> dict:
    """Resolve the top sight without grouping full Sight rows and JSON fields."""
    sight_filters = {"code_id": region_code, "is_pub": True}
    if tourism_type:
        sight_filters["group__tourism_type"] = tourism_type
    eligible_sights = Sight.objects.filter(**sight_filters).values("pk")
    sight_id = (
        AllRegionPopularity.objects.filter(
            sight_id__in=models.Subquery(eligible_sights),
        )
        .values("sight_id")
        .annotate(qty=models.Sum("qty"))
        .order_by(models.F("qty").desc(nulls_last=True), "sight_id")
        .values_list("sight_id", flat=True)
        .first()
    )
    if sight_id is None:
        sight_id = eligible_sights.order_by("pk").values_list("pk", flat=True).first()
    return {"id": sight_id}


def resolve_target_key(
    user,
    home_area: str,
    tourism_type: str,
    candidate_key: str = "",
) -> str:
    """Keep a valid point target or replace it with the area's default target."""
    if home_area == settings.AREA_REGIONS:
        return f"{settings.AREA_REGIONS}_0"

    candidate_kind, candidate_identifier = parse_entity_key(candidate_key)
    if candidate_kind == home_area and candidate_identifier not in (None, "0"):
        try:
            candidate_id = int(candidate_identifier)
        except (TypeError, ValueError):
            candidate_id = 0
        if candidate_id and is_valid_target(
            user.current_region.code,
            home_area,
            candidate_id,
            tourism_type,
        ):
            return f"{home_area}_{candidate_id}"

    return get_default_target_key(user, home_area, tourism_type)


def get_interest_active_cells(table_data: list, source_id) -> tuple:
    """Build the DataTable selection shared by map and table-driven updates."""
    for row_index, row in enumerate(table_data):
        if str(row.get("code")) != str(source_id):
            continue

        columns = ["code__title", "qty_display", "ppt_display"]
        selected_cells = [
            {
                "row": row_index,
                "column": column,
                "column_id": column_id,
                "row_id": row.get("id", row.get("code")),
            }
            for column, column_id in enumerate(columns, start=1)
        ]
        return selected_cells, selected_cells[0]

    return [], None


def get_validated_target_key(state: dict, user) -> str:
    """Return the saved target only while it is available in the restored context."""
    return resolve_target_key(
        user,
        state["homeArea"],
        state["tourismType"],
        state.get("targetKey"),
    )


@interest_app.callback(
    dependencies.Output("updated-link", "data-title"),
    dependencies.Input("interval-background", "n_intervals"),
    prevent_initial_call=False,
)
def update_tooltip(n):
    return generate_update_tooltip_content()


@interest_app.callback(
    dependencies.Output("interest-initial-state", "data"),
    dependencies.Input("helper-interesant", "interval"),
    dependencies.State("interest-session-state", "data"),
)
def initialize_interest_session(interval, persisted_state: dict, **kwargs) -> dict:
    """Create one access-checked snapshot used by every restoration callback."""
    return get_restorable_interest_state(persisted_state, kwargs.get("user"))


def update_interest(
    tourism_type: str,
    home_area: str,
    interesant_area: str,
    map_data: dict,
    target_key: str,
    sort_by: list,
    current_active_cell: dict,
    initial_state: dict = None,
    hydrated: bool = False,
    **kwargs,
):
    """
    Updates interesants table
    :param tourism_type: str
    :param home_area: str
    :param interesant_area: str
    :param map_data: dict
    :param sort_by: list
    :param kwargs: dict
    :return: dict
    """
    user = kwargs.get("user")
    home_area, interesant_area, tourism_type = normalize_interest_context(
        user, home_area, interesant_area, tourism_type
    )
    # TODO processing of an empty table
    selected_cells = []
    active_cell = None
    selected_source_id = None
    clicked_target_key = None
    trigger = get_callback_triggered_id(kwargs.get("callback_context"))
    if trigger == "interest-initial-state" and initial_state:
        sort_by = initial_state.get("sortBy")
    sort_by = normalize_interest_sort(sort_by)
    clicked_key = get_click_entity_key(map_data) if trigger == "map" else None
    clicked_kind, clicked_identifier = parse_entity_key(clicked_key)
    if trigger == "map":
        source_clicked_key = get_source_click_entity_key(map_data)
        source_clicked_kind, source_clicked_identifier = parse_entity_key(
            source_clicked_key
        )
        if source_clicked_key is not None:
            if source_clicked_kind != interesant_area:
                raise PreventUpdate
            selected_source_id = source_clicked_identifier
        elif home_area != settings.AREA_REGIONS and clicked_kind == home_area:
            clicked_target_key = clicked_key
        elif clicked_kind == interesant_area:
            selected_source_id = clicked_identifier
        else:
            raise PreventUpdate
    elif trigger == "table-interesants" and current_active_cell:
        selected_source_id = current_active_cell.get("row_id")
    elif not current_active_cell and not hydrated:
        restored = initial_state or get_restorable_interest_state({}, user)
        if (
            restored["homeArea"] == home_area
            and restored["interesantArea"] == interesant_area
            and restored["tourismType"] == tourism_type
            and restored["sortBy"] == sort_by
        ):
            selected_source_id = restored.get("sourceRowId")

    resolved_target_key = resolve_target_key(
        user,
        home_area,
        tourism_type,
        clicked_target_key or target_key,
    )
    home_id = 0
    target_kind, target_identifier = parse_entity_key(resolved_target_key)
    if (
        home_area != settings.AREA_REGIONS
        and target_kind == home_area
        and target_identifier not in (None, "0")
        and user.is_extended
    ):
        home_id = int(target_identifier)

    table_data = get_ppt_df(
        get_interest_table_rows(
            user.current_region.code,
            home_area,
            interesant_area,
            tourism_type,
            home_id,
        ),
        sort_by,
    ).to_dict("records")

    if selected_source_id is not None:
        selected_cells, active_cell = get_interest_active_cells(
            table_data, selected_source_id
        )
        if active_cell is None and trigger in {"map", "table-interesants"}:
            raise PreventUpdate

    table_state = {
        "homeArea": home_area,
        "interesantArea": interesant_area,
        "tourismType": tourism_type,
        "sortBy": sort_by,
        "sourceRowId": active_cell.get("row_id") if active_cell else None,
        "targetKey": resolved_target_key,
        "mapContextKey": get_interest_map_context_key(
            user.current_region.code,
            home_area,
            interesant_area,
            tourism_type,
            resolved_target_key,
        ),
    }
    return table_data, selected_cells, active_cell, table_state


@interest_app.callback(
    dependencies.Output("table-interesants", "data"),
    dependencies.Output("table-interesants", "selected_cells"),
    dependencies.Output("table-interesants", "active_cell"),
    dependencies.Output("interest-table-state", "data"),
    dependencies.Output("table-interesants", "sort_by"),
    dependencies.Input("tourism-type", "value"),
    dependencies.Input("home-area", "value"),
    dependencies.Input("tabs-interesants", "value"),
    dependencies.Input("map", "clickData"),
    dependencies.Input("home-area-key", "data"),
    dependencies.Input("table-interesants", "sort_by"),
    dependencies.Input("interest-initial-state", "data"),
    dependencies.State("table-interesants", "active_cell"),
    dependencies.State("interest-session-hydrated", "data"),
)
def update_interest_callback(
    tourism_type: str,
    home_area: str,
    interesant_area: str,
    map_data: dict,
    target_key: str,
    sort_by: list,
    initial_state: dict,
    current_active_cell: dict,
    hydrated: bool = False,
    **kwargs,
):
    result = update_interest(
        tourism_type,
        home_area,
        interesant_area,
        map_data,
        target_key,
        sort_by,
        current_active_cell,
        initial_state,
        hydrated,
        **kwargs,
    )
    return (*result, result[3]["sortBy"])


@interest_app.callback(
    dependencies.Output("interest-session-state", "data"),
    dependencies.Input("interest-table-state", "data"),
    dependencies.Input("table-interesants", "active_cell"),
    dependencies.Input("interest-session-hydrated", "data"),
    dependencies.State("table-interesants", "data"),
    dependencies.State("interest-session-state", "data"),
    prevent_initial_call=True,
)
def save_interest_session_state(
    table_state: dict,
    active_cell: dict,
    hydrated: bool,
    table_data: list,
    current_state: dict,
    **kwargs,
) -> dict:
    """Persist the current working context without treating it as authorization."""
    if not hydrated or not table_state:
        raise PreventUpdate
    user = kwargs.get("user")
    home_area = table_state.get("homeArea")
    interesant_area = table_state.get("interesantArea")
    tourism_type = table_state.get("tourismType")
    home_area, interesant_area, tourism_type = normalize_interest_context(
        user, home_area, interesant_area, tourism_type
    )
    sort_by = normalize_interest_sort(table_state.get("sortBy"))
    normalized_target_key = resolve_target_key(
        user,
        home_area,
        tourism_type,
        table_state.get("targetKey"),
    )
    expected_map_context = get_interest_map_context_key(
        user.current_region.code,
        home_area,
        interesant_area,
        tourism_type,
        normalized_target_key,
    )
    if table_state.get("mapContextKey") != expected_map_context:
        raise PreventUpdate

    source_row_id = active_cell.get("row_id") if active_cell else None
    if source_row_id is not None and not any(
        str(row.get("id", row.get("code"))) == str(source_row_id)
        for row in table_data or []
    ):
        source_row_id = None
    state = {
        "version": INTEREST_SESSION_VERSION,
        "regionCode": str(user.current_region.code),
        "homeArea": home_area,
        "interesantArea": interesant_area,
        "tourismType": tourism_type,
        "sortBy": sort_by,
        "sourceRowId": source_row_id,
        "targetKey": normalized_target_key,
    }
    if state == current_state:
        raise PreventUpdate
    return state


@interest_app.callback(
    dependencies.Output("home-area-key", "data"),
    dependencies.Input("home-area", "value"),
    dependencies.Input("map", "clickData"),
    dependencies.Input("tourism-type", "value"),
    dependencies.Input("interest-initial-state", "data"),
    dependencies.State("home-area-key", "data"),
    dependencies.State("interest-session-hydrated", "data"),
)
def update_home_area_key(
    home_area: str,
    map_data: dict,
    tourism_type: str,
    initial_state: dict,
    current_key: str,
    hydrated: bool = False,
    **kwargs,
) -> str:
    """
    :param home_area: str
    :param map_data: dict
    :param kwargs: dict
    :return: str
    """
    user = kwargs.get("user")
    home_area, _, tourism_type = normalize_interest_context(
        user, home_area, settings.AREA_REGIONS, tourism_type
    )
    trigger = get_callback_triggered_id(kwargs.get("callback_context"))

    restored = initial_state or get_restorable_interest_state({}, user)
    restored_matches = (
        restored["homeArea"] == home_area and restored["tourismType"] == tourism_type
    )

    if trigger == "home-area":
        if home_area == settings.AREA_REGIONS:
            return f"{settings.AREA_REGIONS}_0"
        if not hydrated and restored_matches:
            return get_validated_target_key(restored, user)
        return resolve_target_key(user, home_area, tourism_type)

    if trigger == "interest-initial-state":
        return (
            get_validated_target_key(restored, user)
            if restored_matches
            else resolve_target_key(user, home_area, tourism_type)
        )

    if trigger == "map" and get_source_click_entity_key(map_data) is not None:
        raise PreventUpdate

    if trigger == "map" and home_area == settings.AREA_REGIONS:
        raise PreventUpdate

    if trigger == "map" and home_area != settings.AREA_REGIONS:
        clicked_key = get_click_entity_key(map_data)
        clicked_kind, _ = parse_entity_key(clicked_key)
        if clicked_kind == home_area:
            return resolve_target_key(user, home_area, tourism_type, clicked_key)
        raise PreventUpdate

    if trigger == "tourism-type":
        return resolve_target_key(user, home_area, tourism_type, current_key)

    return resolve_target_key(user, home_area, tourism_type, current_key)


@interest_app.callback(
    dependencies.Output("interest-session-hydrated", "data"),
    dependencies.Input("tourism-type", "value"),
    dependencies.Input("home-area", "value"),
    dependencies.Input("tabs-interesants", "value"),
    dependencies.Input("table-interesants", "sort_by"),
    dependencies.Input("home-area-key", "data"),
    dependencies.Input("interest-table-state", "data"),
    dependencies.Input("interest-map-state", "data"),
    dependencies.State("interest-initial-state", "data"),
)
def mark_interest_session_hydrated(
    tourism_type: str,
    home_area: str,
    interesant_area: str,
    sort_by: list,
    target_key: str,
    table_state: dict,
    map_state: dict,
    initial_state: dict,
    **kwargs,
) -> bool:
    """Open persistence only after every restored value has settled."""
    if not initial_state or not table_state or not map_state:
        raise PreventUpdate

    user = kwargs.get("user")
    expected_target_key = get_validated_target_key(initial_state, user)
    expected_context = {
        "homeArea": initial_state["homeArea"],
        "interesantArea": initial_state["interesantArea"],
        "tourismType": initial_state["tourismType"],
        "sortBy": initial_state["sortBy"],
    }
    current_context = {
        "homeArea": home_area,
        "interesantArea": interesant_area,
        "tourismType": tourism_type or "",
        "sortBy": normalize_interest_sort(sort_by),
    }
    table_context = {key: table_state.get(key) for key in expected_context}
    expected_map_context = get_interest_map_context_key(
        user.current_region.code,
        expected_context["homeArea"],
        expected_context["interesantArea"],
        expected_context["tourismType"],
        expected_target_key,
    )
    if not all(
        (
            current_context == expected_context,
            table_context == expected_context,
            target_key == expected_target_key,
            table_state.get("targetKey") == expected_target_key,
            table_state.get("mapContextKey") == expected_map_context,
            map_state.get("ready") is True,
            map_state.get("mapContextKey") == expected_map_context,
            map_state.get("sourceRowId") == table_state.get("sourceRowId"),
        )
    ):
        raise PreventUpdate
    return True


@interest_app.callback(
    dependencies.Output("context-changed", "data"),
    [
        dependencies.Input("table-interesants", "active_cell"),
        dependencies.Input("home-area", "value"),
        dependencies.Input("tourism-type", "value"),
        dependencies.Input("tabs-interesants", "value"),
        dependencies.State("table-interesants", "data"),
        dependencies.State("context-changed", "data"),
    ],
)
def update_context_changed(*args, **kwargs) -> bool:
    """
    :param args: list
    :param kwargs: dict
    :return: bool
    """
    return True


@interest_app.callback(
    dependencies.Output("audience-key", "data"),
    [
        dependencies.Input("table-interesants", "active_cell"),
        dependencies.Input("interest-table-state", "data"),
        dependencies.State("table-interesants", "data"),
        dependencies.State("audience-key", "data"),
    ],
)
def update_audience_key(
    active_cell: dict,
    table_state: dict,
    table_data: list,
    *args,
    **kwargs,
) -> str:
    """
    Updates the audience key
    :param active_cell: dict
    :param tourism_type: str
    :param sort_by: list
    :param interesant_area: str
    :param table_data: dict
    :return: str
    """
    if not table_state:
        raise PreventUpdate
    tourism_type = table_state.get("tourismType") or ""
    interesant_area = table_state.get("interesantArea") or settings.AREA_REGIONS
    sort_by = normalize_interest_sort(table_state.get("sortBy"))

    actual_data = pd.DataFrame(table_data)
    pk = active_cell.get("row_id", "") if active_cell else ""
    if pk:
        return f"{pk}_{tourism_type}_{interesant_area}"

    try:
        sort_columns = [
            {
                "qty_display": "qty",
                "ppt_display": "ppt",
            }.get(item["column_id"], item["column_id"])
            for item in sort_by
        ]
        ascending = [item["direction"] == "asc" for item in sort_by]
        if "code" not in sort_columns:
            sort_columns.append("code")
            ascending.append(True)
        actual_data = actual_data.sort_values(
            sort_columns,
            ascending=ascending,
        )
    except (IndexError, KeyError):
        pass
    try:
        pk = actual_data.iloc[active_cell["row"]].code
    except TypeError:
        pass
    return f"{pk}_{tourism_type}_{interesant_area}"
