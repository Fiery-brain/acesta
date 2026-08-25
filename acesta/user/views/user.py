from urllib.parse import urljoin

from django.conf import settings
from django.contrib import messages
from django.http import FileResponse
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from acesta.front.pdf import document_response
from acesta.front.tracking import build_tracking_url
from acesta.user.apps import DISCOUNTS
from acesta.user.apps import PRICES
from acesta.user.forms import UserForm
from acesta.user.utils import get_order_form
from acesta.user.utils import send_message


@require_POST
def hide_start_modal(request: HttpRequest) -> JsonResponse:
    request.user.is_show_start = False
    request.user.save(update_fields=["is_show_start"])

    return JsonResponse({"status": "ok"})


@require_GET
def dashboard_start_presentation(request: HttpRequest) -> FileResponse:
    return FileResponse(
        open(
            f'{str(settings.APPS_DIR / "templates")}/Tourism-analytics-acesta-presentation.pdf',
            "rb",
        ),
        content_type="application/pdf",
    )


def oferta(request: HttpRequest) -> HttpResponse:
    """
    Public offer
    :param request: HttpRequest
    :return: django.http.HttpResponse
    """
    return document_response(
        request, _render_oferta_html(request), output_format="html"
    )


def oferta_pdf(request: HttpRequest) -> HttpResponse:
    response = document_response(
        request, _render_oferta_html(request), output_format="pdf"
    )
    if response.status_code != 200:
        return response

    region = getattr(request.user, "current_region", "")
    send_message(f"""Загрузка оферты {region} {request.user}""")

    return response


def offer(request: HttpRequest) -> HttpResponse:
    return document_response(request, _render_offer_html(request), output_format="html")


def offer_pdf(request: HttpRequest) -> HttpResponse:
    response = document_response(
        request, _render_offer_html(request), output_format="pdf"
    )
    if response.status_code != 200:
        return response

    send_message(
        f"""Загрузка коммерческого предложения на полный доступ
    {request.user.current_region} {request.user}"""
    )

    return response


def _render_oferta_html(request: HttpRequest) -> str:
    return _render_pdf_template(request, "user/pdf/oferta.html", {})


def _render_offer_html(request: HttpRequest) -> str:
    region = request.user.current_region
    segment = request.user.segment
    tracking_medium = (
        segment if segment and segment != settings.DEFAULT_SEGMENT else "general"
    )
    application_path = reverse("user_order_region", kwargs={"code": region.code})
    application_url = urljoin(
        f"https://{settings.PUBLIC_DOMAIN}/",
        application_path.lstrip("/"),
    )

    def tracked_application_url(content: str) -> str:
        return build_tracking_url(
            application_url,
            source="commercial-offer",
            medium=tracking_medium,
            campaign="full-access",
            content=content,
        )

    context = {
        "TITLE": settings.TITLE,
        "region": region,
        "segment": segment,
        "access_level_columns": ("full",),
        "application_header_url": tracked_application_url("header-logo"),
        "application_qr_url": tracked_application_url("qr"),
        "application_footer_url_page_1": tracked_application_url("page_1"),
        "application_footer_url_page_2": tracked_application_url("page_2"),
        "application_footer_url_page_3": tracked_application_url("page_3"),
    }
    return _render_pdf_template(request, "user/pdf/offer.html", context)


def offer_report(request: HttpRequest) -> HttpResponse:
    return document_response(
        request,
        _render_offer_report_html(request),
        output_format="html",
    )


def offer_report_pdf(request: HttpRequest) -> HttpResponse:
    response = document_response(
        request,
        _render_offer_report_html(request),
        output_format="pdf",
    )
    if response.status_code != 200:
        return response

    send_message(
        f"""Загрузка коммерческого предложения на отчет
    {request.user.current_region} {request.user}"""
    )

    return response


def _render_offer_report_html(request: HttpRequest) -> str:
    region = request.user.current_region
    return _render_pdf_template(
        request,
        "user/pdf/offer_report.html",
        {
            "TITLE": settings.TITLE,
            "region": region,
            "access_level_columns": ("report",),
        },
    )


def _render_pdf_template(
    request: HttpRequest,
    template_name: str,
    context: dict,
) -> str:
    return render_to_string(
        template_name,
        {
            **context,
            "pdf_base_url": request.build_absolute_uri("/"),
        },
        request=request,
    )


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
