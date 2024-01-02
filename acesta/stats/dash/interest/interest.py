from textwrap import wrap

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dependencies
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma

from acesta.stats.dash.helpers.common import get_height_base
from acesta.stats.dash.helpers.interest import get_cities
from acesta.stats.dash.helpers.interest import get_interest
from acesta.stats.dash.helpers.interest import get_map_df
from acesta.stats.dash.helpers.interest import get_ppt_df
from acesta.stats.dash.helpers.interest import get_sights
from acesta.stats.dash.helpers.interest import get_sizes
from acesta.stats.dash.interest.app import interest_app


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
            color_continuous_scale=(
                [
                    "#B2DFDB",
                    "#34766A",
                ]
                if home_area == settings.AREA_REGIONS
                else None
            ),
            color_discrete_sequence=(
                None
                if home_area == settings.AREA_REGIONS
                else [
                    "#dbfffa",
                ]
            ),
            range_color=(20, getattr(df_map, "qty").max()),
            mapbox_style="white-bg"
            if home_area == settings.AREA_REGIONS
            else "open-street-map",
            zoom=(
                kwargs.get("user").current_region.zoom_regions
                if home_area == settings.AREA_REGIONS
                else kwargs.get("user").current_region.zoom_cities
            ),
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
                    color.append(
                        settings.SIGHT_GROUPS_PALETTE.get(sight.group.all()[0].pk)
                    ),
                    ids.append(f"sights_{sight.id}"),
                    title.append(sight.title),
                    extra.append(
                        [
                            ",".join([group.title for group in sight.group.all()]),
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
