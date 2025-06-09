import pandas as pd
from dash import dependencies
from django.conf import settings

from acesta.stats.dash.helpers.interest import generate_update_tooltip_content
from acesta.stats.dash.helpers.interest import get_ppt_df
from acesta.stats.dash.interest.app import interest_app
from acesta.stats.helpers.interest import get_interest


@interest_app.callback(
    dependencies.Output("updated-link", "data-title"),
    dependencies.Input("interval-background", "n_intervals"),
    prevent_initial_call=False,
)
def update_tooltip(n):
    return generate_update_tooltip_content()


@interest_app.callback(
    dependencies.Output("table-interesants", "data"),
    dependencies.Input("tourism-type", "value"),
    dependencies.Input("home-area", "value"),
    dependencies.Input("tabs-interesants", "value"),
    dependencies.Input("map", "clickData"),
    dependencies.Input("table-interesants", "sort_by"),
    dependencies.State("table-interesants", "data"),
)
def update_interest(
    tourism_type: str,
    home_area: str,
    interesant_area: str,
    map_data: dict,
    sort_by: list,
    table_interesants_current_state: dict,
    **kwargs,
):
    """
    Updates interesants table
    :param tourism_type: str
    :param home_area: str
    :param interesant_area: str
    :param map_data: dict
    :param sort_by: list
    :param table_interesants_current_state: dict
    :param kwargs: dict
    :return: dict
    """
    # TODO processing of an empty table
    if map_data and "id" not in map_data.get("points")[0].keys():
        return table_interesants_current_state

    home_id = 0
    if (
        home_area != settings.AREA_REGIONS
        and map_data
        and "id" in map_data.get("points")[0].keys()
        and kwargs.get("user").is_extended
    ):
        home_area, home_id = map_data.get("points")[0].get("id").split("_")

    return get_ppt_df(
        get_interest(
            kwargs.get("user").current_region.code,
            home_area,
            interesant_area,
            tourism_type,
            home_id,
        ),
        sort_by,
    ).to_dict("records")


@interest_app.callback(
    dependencies.Output("home-area-key", "data"),
    [
        dependencies.Input("home-area", "value"),
        dependencies.Input("map", "clickData"),
    ],
)
def update_home_area_key(home_area: str, map_data: dict, **kwargs) -> str:
    """
    :param home_area: str
    :param map_data: dict
    :param kwargs: dict
    :return: str
    """
    home_area_key = f"{settings.AREA_REGIONS}_0"
    if (
        home_area != settings.AREA_REGIONS
        and map_data
        and "id" in map_data.get("points")[0].keys()
        and kwargs.get("user").is_extended
    ):
        home_area_key = map_data.get("points")[0].get("id")
    return f"{home_area_key}"


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
        dependencies.Input("tourism-type", "value"),
        dependencies.Input("table-interesants", "sort_by"),
        dependencies.Input("tabs-interesants", "value"),
        dependencies.State("table-interesants", "data"),
        dependencies.State("audience-key", "data"),
    ],
)
def update_audience_key(
    active_cell: dict,
    tourism_type: str,
    sort_by: list,
    interesant_area: str,
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
    actual_data = pd.DataFrame(table_data)
    pk = ""
    try:
        actual_data = actual_data.sort_values(
            [sort_by[0].get("column_id"), "code"],
            ascending=[True if sort_by[0].get("direction") != "asc" else False, True],
        )
    except (IndexError, KeyError):
        pass
    try:
        pk = actual_data.iloc[active_cell["row"]].code
    except TypeError:
        pass
    return f"{pk}_{tourism_type}_{interesant_area}"
