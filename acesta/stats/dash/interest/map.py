from textwrap import wrap

import plotly.express as px
import plotly.graph_objects as go
from dash import dependencies
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma

from acesta.stats.dash.helpers.common import get_height_base
from acesta.stats.dash.helpers.interest import get_cities
from acesta.stats.dash.helpers.interest import get_map_df
from acesta.stats.dash.helpers.interest import get_sights
from acesta.stats.dash.helpers.interest import get_sizes
from acesta.stats.dash.interest.app import interest_app


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
                ["#B2DFDB", "#34766A"] if home_area == settings.AREA_REGIONS else None
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
