from textwrap import wrap

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table
from dash import dcc
from dash import dependencies
from dash import html
from dash.dash_table.Format import Format
from dash.dash_table.Format import Scheme
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma
from django_plotly_dash import DjangoDash

from acesta.stats.helpers import get_audience
from acesta.stats.helpers import get_audience_key_data
from acesta.stats.helpers import get_cities
from acesta.stats.helpers import get_interest
from acesta.stats.helpers import get_map_df
from acesta.stats.helpers import get_object_title
from acesta.stats.helpers import get_ppt_df
from acesta.stats.helpers import get_sight_stats
from acesta.stats.helpers import get_sights
from acesta.stats.helpers import get_sizes
from acesta.stats.helpers import round_up

app_args = dict(update_title="Загрузка...")


def get_height_base(content_height: str) -> int:
    """
    Returns base height according to client height
    :param content_height: str
    :return: int
    """
    return (
        int(
            (int(content_height) - 140)
            * (int(content_height) - 168)
            / int(content_height)
        )
        - 20
    )


def formatted_percentage(x: int, y: int) -> str:
    """
    Returns formatted result
    :return: str
    """
    return str(int(round(x / y, 2) * 100)).rjust(2)


# Sights Statistics Application
sights_stats_app = DjangoDash("sightStats", **app_args)
sights_stats_app.layout = html.Div(
    [
        html.Div(id="sight-stats", children=[]),
        dcc.Interval(id="helper", n_intervals=0, max_intervals=0, interval=1),
    ]
)


@sights_stats_app.callback(
    dependencies.Output("sight-stats", "children"),
    [dependencies.Input("helper", "interval")],
)
def update_stats_graph(*args, **kwargs) -> dcc.Graph:
    """
    Returns sight stats figure
    :param args: list
    :param kwargs: dict
    :return: dcc.Graph
    """

    def get_df_sight_stats() -> pd.DataFrame:
        """
        Returns sight stats dataframe
        :return: dcc.Graph
        """
        sights_stats = get_sight_stats(kwargs["request"])
        return pd.DataFrame(sights_stats)

    df_sights = get_df_sight_stats()

    color_sequence = [settings.TOURISM_TYPE_PALETTE[name] for name in df_sights.name]

    def get_stats_figure() -> go.Figure:
        """
        Configures sight stats figure
        :return: go.Figure
        """
        height = get_height_base(kwargs.get("request").COOKIES.get("innerHeight")) - 120
        if height < 580:
            height = 580
        fig = px.bar(
            df_sights,
            x="cnt",
            y="title",
            orientation="h",
            color="title",
            color_discrete_sequence=color_sequence,
            text_auto="i",
            text="title",
            labels={"title": "", "cnt": "Количество"},
            height=height,
            custom_data=[
                "groups",
            ],
        )

        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font_family="Nunito",
            font_color="#727070",
            showlegend=False,
            hoverlabel={"bordercolor": "#FFF"},
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                griddash="dot",
                gridcolor="#dedede",
                zeroline=True,
                linewidth=1,
                linecolor="#dedede",
                fixedrange=True,
            ),
            yaxis=dict(ticksuffix="  ", fixedrange=True),
        )

        for d in fig["data"]:
            d.width = 0.5

        fig.update_traces(
            textposition="inside",
            textfont_color="#fff",
            hovertemplate="<br>".join(["%{customdata[0]}", "<extra></extra>"]),
        )

        fig.add_layout_image(
            dict(
                source="/static/img/acesta-ru.png",
                xref="paper",
                yref="paper",
                x=0.86,
                y=-0.05,
                sizex=0.14,
                sizey=0.14,
                opacity=0.9,
            )
        )
        return fig

    return dcc.Graph(
        figure=get_stats_figure(),
        config={"displayModeBar": False, "margin": {"r": 0, "t": 0, "l": 0, "b": 0}},
    )


# Interest Application
interest_app = DjangoDash("interest", **app_args)
interest_app.layout = html.Div(
    className="container",
    children=[
        html.Div(
            className="row mt-4",
            children=[
                html.Div(
                    children=[
                        html.A(
                            id="title-container",
                            href="#",
                            children=[
                                html.H3(
                                    id="title",
                                    children=["Интерес к региону"],
                                    className="fs-6 fw-bolder mb-0 mb-lg-3",
                                )
                            ],
                            className="text-nowrap text-truncate",
                        )
                    ],
                    className="col-12 col-lg-6 col-xl-5 ps-0",
                ),
                html.Div(
                    children=[
                        dcc.Dropdown(
                            id="tourism-type",
                            options=[
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
                            ],
                            clearable=False,
                            value="",
                            className="w-100",
                        )
                    ],
                    className="col-12 col-lg-6 col-xl-7 py-3 py-lg-0 px-0 "
                    "position-relative d-md-flex justify-content-lg-end mb-2",
                ),
            ],
        ),
        html.Div(
            children=[
                dcc.Interval(
                    id="helper-map", n_intervals=0, max_intervals=0, interval=1
                ),
                dcc.Interval(
                    id="helper-interesant", n_intervals=0, max_intervals=0, interval=1
                ),
                dcc.Store(id="audience-key", storage_type="session"),
                html.Div(
                    id="interest",
                    children=[
                        dcc.Tabs(
                            id="tabs-interesants",
                            value=settings.AREA_REGIONS,
                            children=[],
                            className="pt-3 pt-lg-0",
                        ),
                        html.Div(
                            id="tabs-interesants-dummy",
                            children=[],
                        ),
                        html.Div(
                            children=[
                                dash_table.DataTable(
                                    get_ppt_df(
                                        get_interest(
                                            "00",
                                            settings.AREA_REGIONS,
                                            settings.AREA_REGIONS,
                                            "",
                                            0,
                                        ),
                                        [],
                                    ).to_dict("records"),
                                    id="table-interesants",
                                    columns=[
                                        dict(id="code__title", name="", type="str"),
                                        dict(
                                            id="qty",
                                            name="Запросы",
                                            type="numeric",
                                            format=Format().group(True),
                                        ),
                                        dict(
                                            id="ppt",
                                            name="Популярность",
                                            type="numeric",
                                            format=Format(
                                                precision=0, scheme=Scheme.percentage
                                            ).group(True),
                                        ),
                                    ],
                                    page_current=0,
                                    page_size=20000,
                                    page_action="native",
                                    sort_action="custom",
                                    sort_mode="single",
                                    sort_by=[{"column_id": "qty", "direction": "asc"}],
                                    style_data={
                                        "whiteSpace": "normal",
                                        "height": "auto",
                                        "lineHeight": "24px",
                                    },
                                    style_cell_conditional=[
                                        {
                                            "if": {"column_id": "code__title"},
                                            "textAlign": "left",
                                        }
                                    ],
                                    locale_format={"group": " "},
                                )
                            ],
                            id="interest-table-container",
                            className="overflow-auto",
                        ),
                    ],
                    className="col-12 col-lg-6 col-xl-5 px-0",
                ),
                html.Div(
                    id="map-container",
                    children=[
                        html.Div(
                            children=[
                                dcc.RadioItems(
                                    id="home-area",
                                    className="d-flex justify-content-between ps-4 text-nowrap",
                                    value=settings.AREA_REGIONS,
                                ),
                                html.Div(id="home-area-help"),
                            ],
                            className="d-flex justify-content-between",
                        ),
                        html.Div(
                            id="home-area-dummy",
                            children=[],
                        ),
                        html.Div(
                            children=[
                                dcc.Graph(
                                    id="map",
                                    config={
                                        "scrollZoom": True,
                                        "displayModeBar": False,
                                        "doubleClick": "autosize",
                                    },
                                    figure=go.Figure(
                                        layout_yaxis_visible=False,
                                        layout_xaxis_visible=False,
                                        layout=go.Layout(
                                            paper_bgcolor="rgba(0,0,0,0)",
                                            plot_bgcolor="rgba(0,0,0,0)",
                                        ),
                                    ),
                                )
                            ],
                            className="overflow-hidden",
                        ),
                    ],
                    className="col-12 col-lg-6 col-xl-7 overflow-hidden px-0 rounded-2",
                ),
            ],
            className="row d-flex flex-column-reverse flex-lg-row position-relative",
            style={"zIndex": "-1"},
        ),
    ],
)


@interest_app.callback(
    dependencies.Output("title", "children"),
    dependencies.Input("home-area", "value"),
    dependencies.Input("map", "clickData"),
    dependencies.State("title", "children"),
)
def update_title(
    home_area: str, map_data: dict, current_state: str, *args, **kwargs
) -> str:
    """
    Updates the app title
    :param home_area: str
    :param map_data: dict
    :param current_state: str
    :param args: list
    :param kwargs: dict
    :return: str
    """
    pattern = "Интерес к {}"
    if map_data and "id" not in map_data.get("points")[0].keys():
        return current_state

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
                                src="/static/img/dummy-tabs-interesants.svg",
                                width=200,
                            )
                        ],
                        title="Показать цены",
                    )
                ],
            )
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
            # html.Div(
            #    className="border-bottom mb-3",
            # children=[
            html.A(
                href="/price/",
                children=[
                    html.Img(
                        src="/static/img/dummy-home-area.svg",
                        height=36,
                    )
                ],
                title="Показать цены",
            )
            # ]
            # )
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
    current_state: dict,
    **kwargs,
):
    """
    Updates interesants table
    :param tourism_type: str
    :param home_area: str
    :param interesant_area: str
    :param map_data: dict
    :param sort_by: list
    :param current_state: dict
    :param kwargs: dict
    :return: dict
    """
    # TODO processing of an empty table
    if map_data and "id" not in map_data.get("points")[0].keys():
        return current_state

    home_id = 0
    if (
        home_area != settings.AREA_REGIONS
        and map_data
        and "id" in map_data.get("points")[0].keys()
        and kwargs.get("user").is_extended
    ):
        home_area = map_data.get("points")[0].get("id").split("_")[0]
        home_id = map_data.get("points")[0].get("id").split("_")[1]

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
    dependencies.Output("map", "figure"),
    dependencies.Input("tourism-type", "value"),
    dependencies.Input("home-area", "value"),
)
def update_map(tourism_type: str, home_area: str, *args, **kwargs) -> go.Figure:
    """
    Updates the map
    :param tourism_type: str
    :param home_area: str
    :param args: list
    :param kwargs: dict
    :return: dcc.Graph
    """
    base_color = None
    if home_area == settings.AREA_REGIONS:
        base_color = "qty"
    df_map = get_map_df(tourism_type, kwargs.get("user").current_region)
    df_map["qty_str"] = df_map["qty"].apply(lambda x: intcomma(round(x or 0)))
    df_map["ppt_str"] = df_map["ppt"].apply(lambda x: intcomma(round(x or 0)))

    def get_map_figure():
        def get_map_height():
            return (
                get_height_base(kwargs.get("request").COOKIES.get("innerHeight"))
                - 8
                - (99 if kwargs.get("user").is_extended else 65)
            )

        fig = px.choropleth_mapbox(
            df_map,
            geojson=df_map.geometry,
            locations=df_map.index,
            color=base_color,
            color_continuous_scale=[
                "#B2DFDB",
                "#34766A",
            ]
            if home_area == settings.AREA_REGIONS
            else None,
            color_discrete_sequence=None
            if home_area == settings.AREA_REGIONS
            else [
                "#dbfffa",
            ],
            range_color=(20, getattr(df_map, "qty").max()),
            mapbox_style="white-bg"
            if home_area == settings.AREA_REGIONS
            else "open-street-map",
            zoom=kwargs.get("user").current_region.zoom_regions
            if home_area == settings.AREA_REGIONS
            else kwargs.get("user").current_region.zoom_cities,
            center={
                "lat": kwargs.get("user").current_region.center_lat,
                "lon": kwargs.get("user").current_region.center_lon,
            },
            opacity=0.9 if home_area == settings.AREA_REGIONS else 0.45,
            height=get_map_height(),
            custom_data=["name", "qty_str", "ppt_str"],
        )
        fig.add_layout_image(
            dict(
                source="/static/img/acesta-ru.png",
                xref="paper",
                yref="paper",
                x=0.88,
                y=0.1,
                sizex=0.09,
                sizey=0.09,
                opacity=0.8,
            )
        )

        fig.update_traces(
            marker=dict(
                line=dict(
                    color="#ffffff"
                    if home_area == settings.AREA_REGIONS
                    else "#000000",
                    width=0.3,
                ),
            ),
            hovertemplate="<br>".join(
                [
                    "<b>%{customdata[0]}</b><br>",
                    "Запросы: %{customdata[1]}",
                    "Региональная популярность: %{customdata[2]}%",
                    "<extra></extra>",
                ]
            ),
        )

        fig.update_coloraxes(showscale=False)

        if home_area == settings.AREA_CITIES and kwargs.get("user").is_extended:
            cities = get_cities(kwargs.get("user").current_region.code)

            fig.add_trace(
                go.Scattermapbox(
                    lat=[city.lat for city in cities],
                    lon=[city.lon for city in cities],
                    text=[city.title for city in cities],
                    marker={
                        "color": "#F3B869",
                        "size": get_sizes([city.population for city in cities]),
                        "opacity": 0.9,
                    },
                    ids=[f"cities_{city.id}" for city in cities],
                    mode="markers",
                    hovertemplate="<br>".join(
                        ["<b>%{text}</b><br>", "<extra></extra>"]
                    ),
                    showlegend=False,
                )
            )
        elif home_area == settings.AREA_SIGHTS and kwargs.get("user").is_extended:

            sights = get_sights(kwargs.get("user").current_region.code, tourism_type)

            lat = []
            lon = []
            qty = []
            ids = []
            title = []
            extra = []
            color = []
            [
                (
                    lat.append(sight.lat),
                    lon.append(sight.lon),
                    qty.append(sight.qty or 0),
                    color.append(settings.SIGHT_GROUPS_PALETTE.get(sight.group_id)),
                    ids.append(f"sights_{sight.id}"),
                    title.append(sight.title),
                    extra.append(
                        [
                            sight.group.title,
                            "<br>".join(
                                wrap(
                                    sight.address.replace("Россия, ", "").replace(
                                        "Украина, ", ""
                                    ),
                                    45,
                                )
                            ),
                        ]
                    ),
                )
                for sight in sights
            ]

            fig.add_trace(
                go.Scattermapbox(
                    lat=lat,
                    lon=lon,
                    text=title,
                    marker={"color": color, "size": get_sizes(qty), "opacity": 0.8},
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
        fig.update_layout(
            hoverlabel={"font": {"color": "#FFFFFF"}, "bordercolor": "#FFFFFF"},
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            showlegend=False,
        )
        return fig

    return get_map_figure()


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
    :param kwargs: duct
    :return: tuple
    """
    return [], None


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


# Audience Application
audience_app = DjangoDash(
    "audience",
    external_stylesheets=[
        "/static/css/bootstrap.min.css",
        "/static/css/base.css",
        "/static/css/dashboard.css",
    ],
    **app_args,
)
audience_app.layout = html.Div(
    html.Div(
        className="row-flex flex-column bg-white",
        children=[
            dcc.Store(data="", id="audience-key", storage_type="session"),
            html.Div(
                html.H3("", id="audience-title", className="fs-6 fw-bolder ms-1"),
                id="audience-title-container",
                className="bg-white",
            ),
            html.Div(
                id="audience",
                children=[],
                className="col d-flex pt-0 pb-2",
            ),
        ],
    ),
    className="container-fluid p-0",
)


@audience_app.callback(
    dependencies.Output("audience-title", "children"),
    dependencies.Input("audience-key", "data"),
)
def update_audience_title(key, *args, **kwargs):
    pk, _, area = get_audience_key_data(key)

    pattern = "Целевые группы {}"

    if pk:
        if area == settings.AREA_REGIONS:
            title = pattern.format(f" в регионе {get_object_title(pk, area)}")
        else:
            title = pattern.format(f" в городе {get_object_title(pk, area)}")
        return title
    else:
        return ""


@audience_app.callback(
    dependencies.Output("audience-title-container", "className"),
    dependencies.Input("audience-key", "data"),
)
def update_audience_title_style(key, *args, **kwargs):
    pk, _, _ = get_audience_key_data(key)
    if pk:
        return "bg-white d-block pt-3 pb-1"
    else:
        return "d-none"


@audience_app.callback(
    dependencies.Output("audience", "children"),
    dependencies.Input("audience-key", "data"),
)
def update_audience(key, *args, **kwargs):
    pk, tourism_type, area = get_audience_key_data(key)
    if pk and (
        area == settings.AREA_REGIONS
        or (area == settings.AREA_CITIES and kwargs.get("user").is_extended)
    ):
        audience = get_audience(area, tourism_type, pk)
        return [
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.Div(
                                intcomma(
                                    int(round_up(rec.v_type_sex_age * rec.coeff, -3))
                                ),
                                className="audience-qty",
                            ),
                            html.Div(
                                title=f"{dict(settings.TOURISM_TYPES_OUTSIDE).get(rec.tourism_type)}",
                                className=f"audience-tourism-type bg-{rec.tourism_type}",
                                **{"data-bs-toggle": "tooltip"},
                            ),
                        ],
                        className="d-flex justify-content-between",
                    ),
                    html.Div(
                        children=[
                            html.Div(
                                children=[
                                    html.Div(
                                        title=f"{'мужчины' if rec.sex == 'm' else 'женщины'}",
                                        className=f"audience-sex bg-{'man' if rec.sex == 'm' else 'woman'} me-1",
                                        **{"data-bs-toggle": "tooltip"},
                                    ),
                                    html.Span(
                                        f"{rec.age} {'года' if rec.age.endswith('4') else 'лет'}",
                                        className="audience-age",
                                    ),
                                ],
                                className="d-flex",
                            ),
                        ],
                        className="mt-2",
                    ),
                    html.Div(
                        children=[
                            html.P(
                                children=[
                                    "есть пара ",
                                    html.B(
                                        f"{formatted_percentage(rec.v_type_in_pair, rec.v_sex_age)}%"
                                    ),
                                ],
                                className="text-end",
                            ),
                            html.P(
                                children=[
                                    "дети от 6 лет ",
                                    html.B(
                                        f"{formatted_percentage(rec.v_sex_age_child_6, rec.v_sex_age)}%"
                                    ),
                                ],
                                className="text-end",
                            ),
                            html.P(
                                children=[
                                    "дети от 7 до 12 лет ",
                                    html.B(
                                        f"{formatted_percentage(rec.v_sex_age_child_7_12, rec.v_sex_age)}%"
                                    ),
                                ],
                                className="text-end",
                            ),
                            html.P(
                                children=[
                                    "отношения с родителями ",
                                    html.B(
                                        f"{formatted_percentage(rec.v_sex_age_parents, rec.v_sex_age)}%"
                                    ),
                                ],
                                className="mb-0 text-end",
                            ),
                        ],
                        className="mt-2 audience-more",
                        style={"fontSize": "13px"},
                    ),
                ],
                className=f"audience-group me-3 border rounded-2 p-3 border-{rec.tourism_type}",
            )
            for rec in audience
        ]
    else:
        return html.P(
            html.Small(
                f"Выберите заинтересованный "
                f"{'город' if area == settings.AREA_CITIES and kwargs.get('user').is_extended else 'регион'} "
                f"чтобы увидеть целевые группы"
            ),
            className="text-muted pt-2 ps-1",
        )
