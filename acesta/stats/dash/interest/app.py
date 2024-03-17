import plotly.graph_objects as go
from dash import dash_table
from dash import dcc
from dash import html
from dash.dash_table.Format import Format
from dash.dash_table.Format import Scheme
from django.conf import settings
from django_plotly_dash import DjangoDash

from acesta.stats.apps import dash_args
from acesta.stats.dash.helpers.interest import get_interest
from acesta.stats.dash.helpers.interest import get_ppt_df


# Interest Application
interest_app = DjangoDash("interest", **dash_args)
interest_app.layout = html.Div(
    className="container",
    children=[
        html.Div(
            className="row mt-4 position-relative",
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
                            options=[],
                            clearable=False,
                            className="w-100",
                        )
                    ],
                    className=(
                        "col-12 col-lg-6 col-xl-7 py-3 py-lg-0 px-0 "
                        "position-relative d-md-flex justify-content-lg-end mb-2"
                    ),
                ),
            ],
            style={"zIndex": "1"},
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
        ),
    ],
)
