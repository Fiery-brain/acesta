from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import QueryDict
from django.shortcuts import redirect
from django.shortcuts import render

from acesta.user.forms import OrderForm
from acesta.user.pricing import calculate_access_price
from acesta.user.utils import get_support_form
from acesta.user.utils import send_message


def price(request: HttpRequest) -> HttpResponse:
    """
    Price view
    :param request: django.http.HttpRequest
    :return: django.http.HttpResponse
    """
    return render(
        request,
        "user/price.html",
        {
            "access_level_columns": ("basic", "full", "report"),
            "support_form": get_support_form(request.user, settings.SUPPORT_REPORT),
            "conditions_form": get_support_form(
                request.user,
                settings.SUPPORT_CONDITIONS,
            ),
        },
    )


def get_order_data(post: QueryDict) -> tuple:
    """
    Gets order parameters from the POST
    :param post: django.http.QueryDict
    :return: tuple
    """
    district = post.get("federal_district") or None
    try:
        period = float(post.get("period").replace(",", "."))
    except ValueError:
        period = 0
    tourism_types = post.getlist("tourism_types") or post.getlist("tourism_types[]")
    regions = post.getlist("regions") or post.getlist("regions[]")
    return district, period, tourism_types, regions


def new_order(request: HttpRequest) -> HttpResponse:
    """
    Saves a new order
    :param request: django.http.HttpRequest
    :return: django.http.HttpResponse
    """
    if request.POST:
        data = request.POST.copy()

        district, period, tourism_types, regions = get_order_data(request.POST)
        data["period"] = period

        order_form = OrderForm(data=data)

        if order_form.is_valid():
            order = order_form.save(commit=False)
            price = calculate_access_price(
                period,
                regions,
                tourism_types,
                district,
                segment=request.user.segment,
            )
            order.cost = price.cost
            order.discount = price.discount_sum
            order.total = price.total
            order.promotion = price.promotion
            order.promotion_percent = price.promotion_discount
            order.promotion_discount = price.promotion_discount_sum
            if not order.promo:
                order.promo = price.promo_code
            order.save()
            order_form.save_m2m()
            messages.add_message(
                request,
                messages.SUCCESS,
                "Спасибо! Мы получили вашу заявку и&nbsp;обработаем ее в&nbsp;ближайшее время",
            )
            send_message("Новая заявка на расширенный доступ")

        else:
            messages.add_message(
                request,
                messages.ERROR,
                "Не удалось сохранить заявку, попробуйте позже или&nbsp;обратитесь в&nbsp;техподдержку",
            )
            send_message(
                f"Ошибка при добавлении заявки на расширенный доступ {order_form.errors}"
            )

    return redirect("user")


def get_costs(request: HttpRequest) -> JsonResponse:
    """
    Returns a JSON object with calculated
    sums of an order
    :param request: django.http.HttpRequest
    :return: int
    """
    district, period, tourism_types, regions = get_order_data(request.POST)
    price = calculate_access_price(
        period,
        regions,
        tourism_types,
        district,
        segment=request.user.segment,
    )
    return JsonResponse(
        {
            "cost": price.cost,
            "discount": price.period_discount,
            "promotion_discount": price.promotion_discount,
            "promotion_discount_sum": price.promotion_discount_sum,
            "discount_sum": price.discount_sum,
            "total": price.total,
            "promo_code": price.promo_code,
        }
    )
