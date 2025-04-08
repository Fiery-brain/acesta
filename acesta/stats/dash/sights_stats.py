import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc
from dash import dependencies
from dash import html
from django.conf import settings
from django_plotly_dash import DjangoDash

from acesta.stats.apps import dash_args
from acesta.stats.dash.helpers.common import get_height_base
from acesta.stats.helpers.sights import get_sight_stats


# Sights Statistics Application
sights_stats_app = DjangoDash("sightStats", **dash_args)
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
        sights_stats = get_sight_stats(
            code=kwargs.get("request").user.current_region.code
        )
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
            font_family="Golos",
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
