import plotly.graph_objects as go
from dash import dcc
from dash import dependencies
from dash import html
from django.conf import settings

from acesta.stats.apps import AcestaDjangoDash
from acesta.stats.dash.helpers.common import get_height_base
from acesta.stats.helpers.sights import get_sight_stats


# Sights Statistics Application
sights_stats_app = AcestaDjangoDash("sightStats")
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

    sights_stats = get_sight_stats(code=kwargs.get("request").user.current_region.code)

    def get_stats_figure() -> go.Figure:
        """
        Configures sight stats figure
        :return: go.Figure
        """
        height = get_height_base(kwargs.get("request").COOKIES.get("innerHeight")) - 120
        if height < 580:
            height = 580
        fig = go.Figure(
            data=[
                go.Bar(
                    x=[stat["cnt"] for stat in sights_stats],
                    y=[stat["title"] for stat in sights_stats],
                    orientation="h",
                    marker_color=[
                        settings.TOURISM_TYPE_PALETTE[stat["name"]]
                        for stat in sights_stats
                    ],
                    text=[stat["title"] for stat in sights_stats],
                    texttemplate="%{x:i}",
                    customdata=[[stat["groups"]] for stat in sights_stats],
                    width=0.5,
                    hovertemplate="%{customdata[0]}<extra></extra>",
                )
            ]
        )

        fig.update_layout(
            height=height,
            margin={"t": 60},
            paper_bgcolor="white",
            plot_bgcolor="white",
            font_family="Golos",
            font_color="#727070",
            showlegend=False,
            hoverlabel={"bordercolor": "#FFF"},
            xaxis_title="Количество",
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
            yaxis=dict(
                ticksuffix="  ",
                fixedrange=True,
                categoryorder="array",
                categoryarray=[stat["title"] for stat in reversed(sights_stats)],
            ),
        )

        fig.update_traces(
            textposition="inside",
            textfont_color="#fff",
        )

        return fig

    return dcc.Graph(
        figure=get_stats_figure(),
        config={"displayModeBar": False, "margin": {"r": 0, "t": 0, "l": 0, "b": 0}},
    )
