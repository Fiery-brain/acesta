from dash import ClientsideFunction
from dash import dcc
from dash import dependencies
from dash import html
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma

from acesta.stats.apps import AcestaDjangoDash
from acesta.stats.dash.helpers.audience import get_object_title
from acesta.stats.helpers.audience import get_audience
from acesta.stats.helpers.audience import get_audience_key_data
from acesta.stats.helpers.audience import get_audience_quantity
from acesta.stats.helpers.audience import get_indicator_data
from acesta.stats.helpers.audience import prepare_audience_groups
from acesta.stats.helpers.base import formatted_percentage
from acesta.stats.helpers.base import round_up


# Audience Application
audience_app = AcestaDjangoDash(
    "audience",
    external_scripts=[
        "/static/js/bootstrap.bundle.min.js",
        "/static/js/dashboard.audience.tooltips.js",
    ],
    external_stylesheets=[
        "/static/css/bootstrap.min.css",
        "/static/css/base.css",
        "/static/css/dashboard.css",
    ],
)
audience_app.layout = html.Div(
    html.Div(
        className="row-flex flex-column bg-white",
        children=[
            dcc.Store(data="", id="audience-key", storage_type="session"),
            dcc.Store(data={}, id="audience-data"),
            html.Div(
                html.Div(
                    html.H3(
                        "",
                        id="audience-title",
                        className="fs-6 fw-bolder ms-1 text-nowrap",
                    ),
                    className="audience-title-bar",
                ),
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


def update_audience_title(key, *args, **kwargs):
    pk, _, area = get_audience_key_data(key)

    pattern = "Целевые группы по видам туризма {}"

    if pk:
        object_title = get_object_title(pk, area)
        if not object_title:
            return ""
        if area == settings.AREA_REGIONS:
            title = pattern.format(f" в регионе {object_title}")
        else:
            title = pattern.format(f" в городе {object_title}")
        return title
    else:
        return ""


def update_audience_title_style(key, *args, **kwargs):
    pk, _, _ = get_audience_key_data(key)
    if pk:
        return "bg-white d-block"
    else:
        return "d-none"


@audience_app.callback(
    dependencies.Output("audience-title", "children"),
    dependencies.Output("audience-title-container", "className"),
    dependencies.Output("audience-data", "data"),
    dependencies.Input("audience-key", "data"),
)
def update_audience(key, *args, **kwargs):
    pk, tourism_type, area = get_audience_key_data(key)
    user = kwargs.get("user")
    title = update_audience_title(key)
    valid_object = bool(title)
    title_class = update_audience_title_style(key) if valid_object else "d-none"
    if (
        pk
        and (
            area == settings.AREA_REGIONS
            or (area == settings.AREA_CITIES and user.is_extended)
        )
        and valid_object
    ):
        audience, priority_percentile = prepare_audience_groups(
            get_audience(area, tourism_type, pk)
        )
        avg_salary = get_indicator_data(settings.AVERAGE_SALARY, area, pk)
        avg_bill = get_indicator_data(settings.AVERAGE_BILL, area, pk)
        tourism_titles = dict(settings.TOURISM_TYPES_OUTSIDE)
        groups = [
            {
                "q": intcomma(int(round_up(get_audience_quantity(rec), -3))),
                "s": "мужчин" if rec.sex == "m" else "женщин",
                "sc": "men" if rec.sex == "m" else "women",
                "a": f"{rec.age} лет",
                "t": rec.tourism_type,
                "tt": tourism_titles.get(rec.tourism_type),
                "p": f"{formatted_percentage(rec.v_type_in_pair, rec.v_sex_age)}%",
                "c6": f"{formatted_percentage(rec.v_sex_age_child_6, rec.v_sex_age)}%",
                "c12": f"{formatted_percentage(rec.v_sex_age_child_7_12, rec.v_sex_age)}%",
                "pr": f"{formatted_percentage(rec.v_sex_age_parents, rec.v_sex_age)}%",
                "priority": get_audience_quantity(rec) > priority_percentile,
            }
            for rec in audience
        ]
        indicators = {
            "salary": f"{intcomma(int(avg_salary.value))} ₽" if avg_salary else None,
            "bill": f"{intcomma(int(avg_bill.value))} ₽" if avg_bill else None,
            "change": (
                f"{'+' if avg_bill.change > 0 else '-'}{avg_bill.change} %"
                if avg_bill
                else None
            ),
            "changeSign": (
                "+" if avg_bill and avg_bill.change > 0 else "-" if avg_bill else None
            ),
        }
        return title, title_class, {"groups": groups, "indicators": indicators}

    entity = "город" if area == settings.AREA_CITIES and user.is_extended else "регион"
    return (
        title,
        title_class,
        {
            "empty": (
                f"Выберите заинтересованный {entity}, чтобы увидеть целевые группы "
                "туристов. Для этого кликните название в таблице слева."
            )
        },
    )


audience_app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="renderAudience"),
    dependencies.Output("audience", "children"),
    dependencies.Input("audience-data", "data"),
)
