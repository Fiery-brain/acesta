import time

import plotly.graph_objects as go
from dash import dash_table
from dash import dcc
from dash import html
from django.conf import settings
from django_plotly_dash import DjangoDash

from acesta.stats.apps import dash_args


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
                            **{"data-bs-toggle": "tooltip"},
                        )
                    ],
                    className="col-12 col-lg-6 col-xl-5 ps-0",
                ),
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.Div(
                                    dcc.Interval(
                                        id="interval-background",
                                        interval=60 * 1000,
                                        n_intervals=0,
                                    ),
                                    style={"display": "none"},
                                ),
                                html.A(
                                    id="updated-link",
                                    href="#",
                                    key=f"nocache-{time.time()}",
                                    **{
                                        "data-bs-toggle": "tooltip",
                                        "data-bs-html": "true",
                                        "data-title": "",
                                    },
                                    className="ms-3 ms-leg-0 me-0 me-lg-3",
                                ),
                                dcc.Dropdown(
                                    id="tourism-type",
                                    options=[],
                                    clearable=False,
                                    className="w-100",
                                ),
                            ],
                            className="d-flex justify-content-end align-items-center flex-row-reverse flex-lg-row",
                        ),
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
                    id="helper-interesant", n_intervals=0, max_intervals=0, interval=1
                ),
                dcc.Store(id="audience-key", storage_type="session"),
                dcc.Store(data=False, id="context-changed", storage_type="session"),
                dcc.Store(data="", id="home-area-key"),
                dcc.Store(data={}, id="interest-session-state", storage_type="session"),
                dcc.Store(data=None, id="interest-initial-state"),
                dcc.Store(data=None, id="interest-table-state"),
                dcc.Store(data=False, id="interest-session-hydrated"),
                dcc.Store(data={}, id="interest-map-viewport"),
                dcc.Store(data={}, id="interest-map-camera"),
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
                                    [],
                                    id="table-interesants",
                                    columns=[
                                        dict(
                                            id="history_action",
                                            name="",
                                            type="text",
                                            presentation="markdown",
                                        ),
                                        dict(id="code__title", name="", type="str"),
                                        dict(
                                            id="qty_display",
                                            name="Запросы",
                                            type="text",
                                            presentation="markdown",
                                        ),
                                        dict(
                                            id="ppt_display",
                                            name="Популярность",
                                            type="text",
                                            presentation="markdown",
                                        ),
                                    ],
                                    markdown_options={"html": True},
                                    page_current=0,
                                    page_size=20000,
                                    page_action="native",
                                    sort_action="custom",
                                    sort_mode="single",
                                    sort_by=[
                                        {
                                            "column_id": "qty_display",
                                            "direction": "desc",
                                        }
                                    ],
                                    style_data={
                                        "whiteSpace": "normal",
                                        "height": "auto",
                                        "lineHeight": "24px",
                                    },
                                    style_cell_conditional=[
                                        {
                                            "if": {"column_id": "code__title"},
                                            "textAlign": "left",
                                        },
                                        {
                                            "if": {
                                                "column_id": [
                                                    "qty_display",
                                                    "ppt_display",
                                                ]
                                            },
                                            "textAlign": "right",
                                        },
                                        {
                                            "if": {"column_id": "history_action"},
                                            "textAlign": "center",
                                            "width": "38px",
                                            "minWidth": "38px",
                                            "maxWidth": "38px",
                                            "padding": "0",
                                        },
                                    ],
                                    style_data_conditional=[
                                        {
                                            "if": {
                                                "filter_query": "{ppt} >= 1 && {ppt} < 10",
                                                "column_id": "ppt_display",
                                            },
                                            "color": "#429388",
                                            # "fontWeight": "600",
                                        },
                                        {
                                            "if": {
                                                "filter_query": "{ppt} >= 10",
                                                "column_id": "ppt_display",
                                            },
                                            "color": "#429388",
                                        },
                                        {
                                            "if": {
                                                "filter_query": "{ppt} > 10",
                                                "column_id": [
                                                    "code__title",
                                                    "qty_display",
                                                    "ppt_display",
                                                ],
                                            },
                                            "fontWeight": "700",
                                        },
                                        {
                                            "if": {
                                                "filter_query": "{ppt} >= 1 && {ppt} < 10",
                                                "column_id": [
                                                    "code__title",
                                                    "qty_display",
                                                    "ppt_display",
                                                ],
                                            },
                                            "fontWeight": "500",
                                        },
                                        {
                                            "if": {
                                                "filter_query": "{ppt} < 1",
                                                "column_id": [
                                                    "code__title",
                                                    "qty_display",
                                                    "ppt_display",
                                                ],
                                            },
                                            "color": "#8c9fa7",
                                        },
                                    ],
                                    locale_format={"group": " "},
                                    css=[
                                        {
                                            "selector": 'th[data-dash-column="history_action"]',
                                            "rule": (
                                                "pointer-events:none;width:38px;"
                                                "min-width:38px;max-width:38px;padding:0;"
                                                "cursor:default;background-image:none;"
                                            ),
                                        },
                                        {
                                            "selector": (
                                                'th[data-dash-column="history_action"] '
                                                ".column-header--sort"
                                            ),
                                            "rule": "display:none!important;",
                                        },
                                        {
                                            "selector": (
                                                'th[data-dash-column="history_action"] '
                                                ".column-header-name"
                                            ),
                                            "rule": "display:none!important;",
                                        },
                                        {
                                            "selector": 'td[data-dash-column="history_action"] p',
                                            "rule": "margin:0;display:flex;align-items:center;justify-content:center;",
                                        },
                                    ],
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
                                        "displayModeBar": True,
                                        "displaylogo": False,
                                        "locale": "ru",
                                        "modeBarButtons": [["zoomInMap", "zoomOutMap"]],
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
                                ),
                                html.Div(
                                    id="interest-map-balloons",
                                    className="interest-map-balloons",
                                    children=[],
                                    **{"aria-live": "polite"},
                                ),
                                html.Aside(
                                    id="region-current-card",
                                    className="region-current-card",
                                    children=[
                                        html.Div(id="region-current-card-content"),
                                        html.Div(
                                            className="region-current-card__actions",
                                            children=[
                                                html.Button(
                                                    html.Span(
                                                        className=(
                                                            "region-current-card__"
                                                            "toggle-icon"
                                                        ),
                                                        **{"aria-hidden": "true"},
                                                    ),
                                                    id="region-current-card-toggle",
                                                    className=(
                                                        "region-current-card__control "
                                                        "region-current-card__toggle"
                                                    ),
                                                    type="button",
                                                    title="Свернуть карточку региона",
                                                    **{
                                                        "aria-label": (
                                                            "Свернуть карточку региона"
                                                        ),
                                                        "aria-expanded": "true",
                                                    },
                                                ),
                                                html.Button(
                                                    html.Span(
                                                        className=(
                                                            "region-current-card__"
                                                            "close-icon"
                                                        ),
                                                        **{"aria-hidden": "true"},
                                                    ),
                                                    id="region-current-card-close",
                                                    className=(
                                                        "region-current-card__control "
                                                        "region-current-card__close"
                                                    ),
                                                    type="button",
                                                    title="Закрыть карточку региона",
                                                    **{
                                                        "aria-label": (
                                                            "Закрыть карточку региона"
                                                        )
                                                    },
                                                ),
                                            ],
                                        ),
                                    ],
                                    **{"aria-live": "polite"},
                                ),
                            ],
                            className=(
                                "interest-map-stage position-relative "
                                "overflow-hidden"
                            ),
                        ),
                    ],
                    className="col-12 col-lg-6 col-xl-7 overflow-hidden px-0 rounded-2",
                ),
            ],
            className="row d-flex flex-column-reverse flex-lg-row position-relative",
        ),
    ],
)
