from dash import dcc
from dash import dependencies
from dash import html
from dash.exceptions import PreventUpdate
from django.conf import settings

from acesta.geo.models import City
from acesta.geo.models import Sight
from acesta.stats.dash.interest.app import interest_app
from acesta.stats.dash.interest.interest import resolve_target_key
from acesta.stats.dash.interest.map_connections import parse_entity_key


def get_interest_table_columns(interesant_area: str) -> list[dict]:
    """Return table columns with a source-specific entity heading."""
    entity_heading = "Город" if interesant_area == settings.AREA_CITIES else "Регион"
    return [
        {
            "id": "history_action",
            "name": "",
            "type": "text",
            "presentation": "markdown",
        },
        {"id": "code__title", "name": entity_heading, "type": "str"},
        {
            "id": "qty_display",
            "name": "Запросы",
            "type": "text",
            "presentation": "markdown",
        },
        {
            "id": "ppt_display",
            "name": "Популярность",
            "type": "text",
            "presentation": "markdown",
        },
    ]


@interest_app.callback(
    dependencies.Output("table-interesants", "columns"),
    dependencies.Input("tabs-interesants", "value"),
)
def update_interest_table_columns(interesant_area: str) -> list[dict]:
    return get_interest_table_columns(interesant_area)


@interest_app.callback(
    dependencies.Output("title", "children"),
    dependencies.Input("home-area", "value"),
    dependencies.Input("home-area-key", "data"),
    dependencies.Input("tourism-type", "value"),
)
def update_title(
    home_area: str,
    target_key: str,
    tourism_type: str,
    *args,
    **kwargs,
) -> str:
    """Build the title from the persistent, server-validated target key."""
    user = kwargs.get("user")
    if not user.is_extended or home_area == settings.AREA_REGIONS:
        return "Интерес к региону"

    target_key = resolve_target_key(user, home_area, tourism_type, target_key)
    target_kind, target_identifier = parse_entity_key(target_key)
    if target_kind != home_area or target_identifier in (None, "0"):
        return "Интерес к региону"

    if home_area == settings.AREA_CITIES:
        target = City.objects.filter(
            pk=target_identifier,
            code_id=user.current_region.code,
        ).first()
        return f"Интерес к городу {target.title}" if target else "Интерес к региону"

    filters = {
        "pk": target_identifier,
        "code_id": user.current_region.code,
        "is_pub": True,
    }
    if tourism_type:
        filters["group__tourism_type"] = tourism_type
    target = Sight.objects.filter(**filters).first()
    return f"Интерес к объекту {target.title}" if target else "Интерес к региону"


@interest_app.callback(
    dependencies.Output("tabs-interesants", "children"),
    dependencies.Output("tabs-interesants", "value"),
    dependencies.Input("interest-initial-state", "data"),
)
def update_tabs(initial_state, *args, **kwargs):
    """
    Returns interesants area tabs
    :param kwargs:
    :return:
    """
    if not initial_state:
        raise PreventUpdate
    if kwargs.get("user").is_extended:
        values = {settings.AREA_REGIONS, settings.AREA_CITIES}
        restored_value = initial_state.get("interesantArea")
        return (
            [
                dcc.Tab(label="из регионов", value=settings.AREA_REGIONS),
                dcc.Tab(label="из городов", value=settings.AREA_CITIES),
            ],
            restored_value if restored_value in values else settings.AREA_REGIONS,
        )
    else:
        return [], settings.AREA_REGIONS


@interest_app.callback(
    dependencies.Output("tabs-interesants-dummy", "children"),
    dependencies.Input("helper-interesant", "interval"),
)
def update_interesants_dummy(*args, **kwargs):
    """
    Returns interesants area tabs
    :param kwargs:
    :return: list
    """
    if kwargs.get("user").is_extended:
        return []
    else:
        return [
            html.Div(
                className="border-bottom mb-3",
                children=[
                    html.A(
                        href="/price/",
                        children=[
                            html.Img(
                                src="/static/img/dummy-tabs-interesants.svg", width=230
                            )
                        ],
                        title="Управлять доступом",
                        **{"data-bs-toggle": "tooltip"},
                    )
                ],
            )
        ]


def get_tourism_type_options(user, home_area: str) -> list[dict]:
    """Return the complete tourism dictionary with access flags applied."""
    if (
        user.is_extended
        and home_area != settings.AREA_REGIONS
        and user.is_set_tourism_types
    ):
        return [
            {
                "value": name,
                "search": title,
                "label": html.Span(
                    className=(
                        f"option bg-{name}"
                        f"{' disabled' if name not in user.tourism_types else ''}"
                    ),
                    children=[title],
                ),
                "disabled": name not in user.tourism_types,
            }
            for name, title in settings.TOURISM_TYPES_OUTSIDE
        ]

    return [
        {
            "value": "",
            "label": html.Span(
                className="option",
                children=["все виды туризма"],
            ),
        },
        *[
            {
                "value": name,
                "search": title,
                "label": html.Span(
                    className=f"option bg-{name}",
                    children=[title],
                ),
            }
            for name, title in settings.TOURISM_TYPES_OUTSIDE
        ],
    ]


@interest_app.callback(
    dependencies.Output("tourism-type", "options"),
    dependencies.Output("tourism-type", "value"),
    dependencies.Input("home-area", "value"),
    dependencies.Input("interest-initial-state", "data"),
    dependencies.State("tourism-type", "value"),
    dependencies.State("interest-session-hydrated", "data"),
)
def update_tourism_type(
    home_area: str,
    initial_state: dict,
    current_tourism_type: str,
    hydrated: bool = False,
    **kwargs,
) -> tuple[list[dict], str]:
    """Set tourism options and value atomically after the area has settled."""
    if not initial_state:
        raise PreventUpdate

    user = kwargs.get("request").user
    options = get_tourism_type_options(user, home_area)

    if not hydrated:
        if initial_state.get("homeArea") != home_area:
            raise PreventUpdate
        tourism_type = initial_state.get("tourismType") or ""
    else:
        tourism_type = current_tourism_type or ""
        if home_area != settings.AREA_REGIONS and user.is_set_tourism_types:
            tourism_type = user.get_current_tourism_type(tourism_type)

    return options, tourism_type


@interest_app.callback(
    dependencies.Output("home-area", "options"),
    dependencies.Output("home-area", "value"),
    dependencies.Input("interest-initial-state", "data"),
)
def update_options(initial_state, *args, **kwargs):
    if not initial_state:
        raise PreventUpdate
    if kwargs.get("request").user.is_extended:
        options = [
            {
                "value": settings.AREA_REGIONS,
                "label": html.Div(
                    [html.Div("регион", className="ps-1")],
                    className="d-inline-block me-4",
                ),
            }
        ]
        if (
            kwargs.get("user").current_region.region_type
            != settings.REGION_TYPE_FEDERAL_CITY
        ):
            options.append(
                {
                    "value": settings.AREA_CITIES,
                    "label": html.Div(
                        [html.Div("города")], className="d-inline-block me-4"
                    ),
                }
            )
        options.append(
            {
                "value": settings.AREA_SIGHTS,
                "label": html.Div(
                    [
                        html.Div("точки", className="ps-1"),
                        html.Div(" притяжения", className="d-none d-lg-inline ps-1"),
                    ],
                    className="d-inline-flex",
                ),
            }
        )
        allowed_values = {option["value"] for option in options}
        restored_value = initial_state.get("homeArea")
        return (
            options,
            (
                restored_value
                if restored_value in allowed_values
                else settings.AREA_REGIONS
            ),
        )
    else:
        return [], settings.AREA_REGIONS


@interest_app.callback(
    dependencies.Output("home-area-dummy", "children"),
    dependencies.Input("helper-interesant", "interval"),
)
def update_home_area_dummy(*args, **kwargs):
    """
    Returns interesants area tabs
    :param kwargs:
    :return:
    """
    if kwargs.get("user").is_extended:
        return []
    else:
        return [
            html.A(
                href="/price/",
                children=[html.Img(src="/static/img/dummy-home-area.svg", height=36)],
                title="Управлять доступом",
                **{"data-bs-toggle": "tooltip"},
            )
        ]
