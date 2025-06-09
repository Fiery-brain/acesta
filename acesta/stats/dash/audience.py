from dash import dcc
from dash import dependencies
from dash import html
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma
from django_plotly_dash import DjangoDash

from acesta.stats.apps import dash_args
from acesta.stats.dash.helpers.audience import get_object_title
from acesta.stats.helpers.audience import get_audience
from acesta.stats.helpers.audience import get_audience_key_data
from acesta.stats.helpers.audience import get_indicator_data
from acesta.stats.helpers.base import formatted_percentage
from acesta.stats.helpers.base import round_up


# Audience Application
audience_app = DjangoDash(
    "audience",
    external_stylesheets=[
        "/static/css/bootstrap.min.css",
        "/static/css/base.css",
        "/static/css/dashboard.css",
    ],
    **dash_args,
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
        avg_salary = get_indicator_data(settings.AVERAGE_SALARY, area, pk)
        avg_bill = get_indicator_data(settings.AVERAGE_BILL, area, pk)
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
                                    "дети до 6 лет ",
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
                                    "отношения ",
                                    html.Span(
                                        "с родителями ",
                                        className="d-none d-lg-inline",
                                    ),
                                    html.Span(
                                        "с род. ",
                                        className="d-inline d-lg-none",
                                    ),
                                    html.B(
                                        f"{formatted_percentage(rec.v_sex_age_parents, rec.v_sex_age)}%"
                                    ),
                                ],
                                className="mb-0 text-end",
                            ),
                            html.Hr() if avg_salary or avg_bill else None,
                            (
                                html.P(
                                    children=[
                                        html.Span(
                                            "средняя зарплата ",
                                            className="d-none d-lg-inline",
                                        ),
                                        html.Span(
                                            "ср. зарплата ",
                                            className="d-inline d-lg-none",
                                        ),
                                        html.Strong(
                                            f"{intcomma(int(avg_salary.value))} ₽"
                                        ),
                                    ],
                                    className="mb-0 text-end",
                                )
                                if avg_salary
                                else None
                            ),
                            (
                                html.P(
                                    children=[
                                        html.Span(
                                            "средний чек ",
                                            className="d-none d-lg-inline",
                                        ),
                                        html.Span(
                                            "ср. чек ",
                                            className="d-inline d-lg-none",
                                        ),
                                        html.Strong(
                                            f"{intcomma(int(avg_bill.value))} ₽"
                                        ),
                                    ],
                                    className="mb-0 text-end",
                                )
                                if avg_bill
                                else None
                            ),
                            (
                                html.P(
                                    children=[
                                        html.Span(
                                            "изменение среднего чека ",
                                            className="d-none d-xl-inline",
                                        ),
                                        html.Span(
                                            "изменение ср. чека ",
                                            className="d-none d-lg-inline d-xl-none",
                                        ),
                                        html.Span(
                                            "изм. ср. чека ",
                                            className="d-inline d-lg-none",
                                        ),
                                        html.Strong(
                                            f"{'+' if avg_bill.change > 0 else '-'}"
                                            f"{avg_bill.change} %",
                                            **{
                                                "data-value": f"{'+' if avg_bill.change > 0 else '-'}"
                                            },
                                            className="colored-percentage",
                                        ),
                                    ],
                                    className="mb-0 text-end",
                                )
                                if avg_bill
                                else None
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
                "Выберите заинтересованный "
                f"{'город' if area == settings.AREA_CITIES and kwargs.get('user').is_extended else 'регион'}, "
                "чтобы увидеть целевые группы туристов. Для этого кликните название в таблице слева."
            ),
            className="text-muted pt-2 ps-1",
        )
