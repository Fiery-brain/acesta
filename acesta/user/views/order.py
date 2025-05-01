from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import QueryDict
from django.shortcuts import redirect
from django.shortcuts import render

from acesta.user.apps import DISCOUNTS
from acesta.user.apps import PRICES
from acesta.user.forms import OrderForm
from acesta.user.models import Order
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
            "price_region": Order.get_cost(
                0.25,
                [request.user.current_region.code],
                [settings.TOURISM_TYPE_DEFAULT],
            ),
            "price_district": Order.get_cost(
                0.25,
                None,
                [settings.TOURISM_TYPE_DEFAULT],
                request.user.current_region.federal_district,
            ),
            "prices": PRICES,
            "discounts": DISCOUNTS,
            "support_form": get_support_form(request.user, settings.SUPPORT_REPORT),
        },
    )


def get_order_data(post: QueryDict) -> tuple:
    """
    Gets order parameters from the POST
    :param post: django.http.QueryDict
    :return: tuple
    """
    district = post.get("district") or None
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
            order.cost = Order.get_cost(period, regions, tourism_types, district)
            order.discount = Order.get_discount_sum(period, regions, tourism_types)
            order.total = order.cost - order.discount
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
    return JsonResponse(
        {
            "cost": Order.get_cost(period, regions, tourism_types, district),
            "discount": Order.get_discount(period),
            "discount_sum": Order.get_discount_sum(period, regions, tourism_types),
        }
    )
