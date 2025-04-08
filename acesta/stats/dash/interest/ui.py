from dash import dcc
from dash import dependencies
from dash import html
from django.conf import settings

from acesta.stats.dash.helpers.common import get_height_base
from acesta.stats.dash.interest.app import interest_app


@interest_app.callback(
    dependencies.Output("title", "children"),
    dependencies.Input("home-area", "value"),
    dependencies.Input("map", "clickData"),
    dependencies.State("title", "children"),
)
def update_title(
    home_area: str, map_data: dict, title_current_state: str, *args, **kwargs
) -> str:
    """
    Updates the app title
    :param home_area: str
    :param map_data: dict
    :param title_current_state: str
    :param args: list
    :param kwargs: dict
    :return: str
    """
    pattern = "Интерес к {}"
    if map_data and "id" not in map_data.get("points")[0].keys():
        return title_current_state

    title = pattern.format("региону")
    if (
        home_area != settings.AREA_REGIONS
        and map_data
        and "id" in map_data.get("points")[0].keys()
        and kwargs.get("user").is_extended
    ):
        if map_data.get("points")[0].get("id").split("_")[0] == settings.AREA_CITIES:
            title = pattern.format(f"городу {map_data.get('points')[0].get('text')}")
        elif map_data.get("points")[0].get("id").split("_")[0] == settings.AREA_SIGHTS:
            title = pattern.format(f"объекту {map_data.get('points')[0].get('text')}")
    return title


@interest_app.callback(
    dependencies.Output("tabs-interesants", "children"),
    dependencies.Input("helper-interesant", "interval"),
)
def update_tabs(*args, **kwargs):
    """
    Returns interesants area tabs
    :param kwargs:
    :return:
    """
    if kwargs.get("user").is_extended:
        return [
            dcc.Tab(label="Регионы", value=settings.AREA_REGIONS),
            dcc.Tab(label="Города", value=settings.AREA_CITIES),
        ]
    else:
        return []


@interest_app.callback(
    dependencies.Output("tabs-interesants-dummy", "children"),
    dependencies.Input("helper-interesant", "interval"),
)
def update_interesants_dummy(*args, **kwargs):
    """
    Returns interesants area tabs
    :param kwargs:
    :return:
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
                                src="/static/img/dummy-tabs-interesants.svg", width=200
                            )
                        ],
                        title="Показать цены",
                    )
                ],
            )
        ]


@interest_app.callback(
    dependencies.Output("tourism-type", "value"),
    dependencies.Input("home-area", "value"),
)
def update_tourism_type(home_area: str, **kwargs):
    if (
        kwargs.get("request").user.is_extended
        and home_area != settings.AREA_REGIONS
        and kwargs.get("request").user.is_set_tourism_types
    ):
        return kwargs.get("request").user.get_current_tourism_type()
    else:
        return ""


@interest_app.callback(
    dependencies.Output("tourism-type", "options"),
    dependencies.Input("home-area", "value"),
)
def update_tourism_types(home_area: str, **kwargs):
    if (
        kwargs.get("request").user.is_extended
        and home_area != settings.AREA_REGIONS
        and kwargs.get("request").user.is_set_tourism_types
    ):
        return [
            {
                "value": name,
                "search": title,
                "label": html.Span(
                    className=(
                        f"option bg-{name}{' disabled' if name not in kwargs.get('request').user.tourism_types else ''}"
                    ),
                    children=[title],
                ),
                "disabled": True
                if name not in kwargs.get("request").user.tourism_types
                else False,
            }
            for name, title in settings.TOURISM_TYPES_OUTSIDE
        ]
    else:
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
    dependencies.Output("home-area", "options"),
    dependencies.Input("helper-interesant", "interval"),
)
def update_options(*args, **kwargs):
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
        return options
    else:
        return []


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
                title="Показать цены",
            )
        ]


@interest_app.callback(
    dependencies.Output("interest-table-container", "style"),
    dependencies.Input("helper-interesant", "interval"),
)
def update_table_style(*args, **kwargs):
    tabsHeight = 54 if kwargs.get("user").is_extended else 0
    return {
        "maxHeight": f"{get_height_base(kwargs.get('request').COOKIES.get('innerHeight')) - tabsHeight - 8 - 66}px"
    }


@interest_app.callback(
    dependencies.Output("table-interesants", "selected_cells"),
    dependencies.Output("table-interesants", "active_cell"),
    dependencies.Input("tabs-interesants", "value"),
    dependencies.Input("tourism-type", "value"),
    dependencies.Input("map", "clickData"),
)
def clear(*args, **kwargs) -> tuple:
    """
    Resets selected data in interesants table
    :param args: list
    :param kwargs: dict
    :return: tuple
    """
    return [], None
