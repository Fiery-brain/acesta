from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa

from acesta.user.apps import DISCOUNTS
from acesta.user.apps import PRICES
from acesta.user.forms import UserForm
from acesta.user.models import Order
from acesta.user.utils import fetch_pdf_resources
from acesta.user.utils import get_order_form
from acesta.user.utils import send_message


def oferta(request: HttpRequest) -> HttpResponse:
    """
    Public offer
    :param request: HttpRequest
    :return: django.http.HttpResponse
    """
    template = get_template("user/oferta.html")

    html = template.render({})

    pdf = BytesIO()
    pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")),
        pdf,
        encoding="utf-8",
        link_callback=fetch_pdf_resources,
    )

    response = HttpResponse(pdf.getvalue(), content_type="application/pdf")
    response[
        "Content-Disposition"
    ] = f"attachment; filename=acesta-offer-{timezone.now().strftime('%d.%m.%Y')}.pdf"

    send_message(f"""Загрузка оферты {request.user.current_region} {request.user}""")

    return response


def offer(request: HttpRequest) -> HttpResponse:
    template = get_template("user/offer.html")

    district = request.user.current_region.federal_district
    district_title = dict(settings.FEDERAL_DISTRICTS).get(district)
    regions = [request.user.current_region.code]
    html = template.render(
        {
            "TITLE": settings.TITLE,
            "discounts": DISCOUNTS,
            "region": request.user.current_region,
            "cost_1w_1t": Order.get_cost(
                0.25, regions, [settings.TOURISM_TYPE_DEFAULT]
            ),
            "cost_1w": Order.get_cost(0.25, regions),
            "cost_1m_1t": Order.get_cost(1, regions, [settings.TOURISM_TYPE_DEFAULT]),
            "cost_1m": Order.get_cost(1, regions),
            "cost_6m_1t": int(
                Order.get_cost(6, regions, [settings.TOURISM_TYPE_DEFAULT])
                - Order.get_discount_sum(6, regions, [settings.TOURISM_TYPE_DEFAULT])
            ),
            "cost_6m": int(
                Order.get_cost(6, regions) - Order.get_discount_sum(6, regions)
            ),
            "cost_12m_1t": int(
                Order.get_cost(12, regions, [settings.TOURISM_TYPE_DEFAULT])
                - Order.get_discount_sum(12, regions, [settings.TOURISM_TYPE_DEFAULT])
            ),
            "cost_12m": int(
                Order.get_cost(12, regions) - Order.get_discount_sum(12, regions)
            ),
            "district_title": district_title,
            "cost_district_1w_1t": Order.get_cost(
                0.25, None, [settings.TOURISM_TYPE_DEFAULT], district
            ),
            "cost_district_1w": Order.get_cost(0.25, None, None, district),
            "cost_district_1m_1t": Order.get_cost(
                1, None, [settings.TOURISM_TYPE_DEFAULT], district
            ),
            "cost_district_1m": Order.get_cost(1, None, None, district),
            "cost_district_6m_1t": int(
                Order.get_cost(6, None, [settings.TOURISM_TYPE_DEFAULT], district)
                - Order.get_discount_sum(
                    6, None, [settings.TOURISM_TYPE_DEFAULT], district
                )
            ),
            "cost_district_6m": int(
                Order.get_cost(6, None, None, district)
                - Order.get_discount_sum(6, None, None, district)
            ),
            "cost_district_12m_1t": int(
                Order.get_cost(12, None, [settings.TOURISM_TYPE_DEFAULT], district)
                - Order.get_discount_sum(
                    12, None, [settings.TOURISM_TYPE_DEFAULT], district
                )
            ),
            "cost_district_12m": int(
                Order.get_cost(12, None, None, district)
                - Order.get_discount_sum(12, None, None, district)
            ),
        }
    )

    pdf = BytesIO()
    pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")),
        pdf,
        encoding="utf-8",
        link_callback=fetch_pdf_resources,
    )

    response = HttpResponse(pdf.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = (
        f"attachment; filename=acesta-offer-{request.user.current_region.code}"
        f"-{timezone.now().strftime('%d.%m.%Y')}.pdf"
    )

    send_message(
        f"""Загрузка коммерческого предложения на полный доступ
    {request.user.current_region} {request.user}"""
    )

    return response


def offer_report(request: HttpRequest) -> HttpResponse:
    template = get_template("user/offer_report.html")

    region = request.user.current_region
    html = template.render({"TITLE": settings.TITLE, "region": region})

    pdf = BytesIO()
    pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")),
        pdf,
        encoding="utf-8",
        link_callback=fetch_pdf_resources,
    )

    response = HttpResponse(pdf.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = (
        f"attachment; filename=acesta-offer-report-{request.user.current_region.code}"
        f"-{timezone.now().strftime('%d.%m.%Y')}.pdf"
    )

    send_message(
        f"""Загрузка коммерческого предложения на отчет
    {request.user.current_region} {request.user}"""
    )

    return response


def user_profile(
    request: HttpRequest, code: str = None, district: str = None
) -> HttpResponse:
    """
    User's Profile representation
    :param request: django.http.HttpRequest
    :param code: str
    :param district: str
    :return: django.http.HttpResponse
    """
    if request.POST:
        user_form = UserForm(instance=request.user, data=request.POST)
        if user_form.is_valid():
            user_form.save()
            messages.add_message(
                request, messages.SUCCESS, "Ваши данные успешно сохранены"
            )
        else:
            messages.add_message(
                request,
                messages.ERROR,
                "Не удалось сохранить данные, попробуйте позже или&nbsp;обратитесь в&nbsp;техподдержку",
            )
            send_message(f"Ошибка при сохранении данных {user_form.errors}")

    return render(
        request,
        "user/user.html",
        {
            "prices": PRICES,
            "discounts": DISCOUNTS,
            "tourism_types": settings.TOURISM_TYPES_OUTSIDE,
            "order_form": get_order_form(request.user),
            "user_form": UserForm(instance=request.user),
            "code": code,
            "district": district,
        },
    )
