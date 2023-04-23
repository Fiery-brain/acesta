from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import QueryDict
from django.shortcuts import redirect
from django.shortcuts import render
from sentry_sdk import capture_message

from acesta.geo.models import Region
from acesta.user.forms import OrderForm
from acesta.user.forms import SupportForm
from acesta.user.forms import UserForm
from acesta.user.models import Order
from acesta.user.utils import get_order_form
from acesta.user.utils import get_support_form


PRICES = {
    "rank_0": 0,
    "rank_1": settings.PRICES.get("rank_1"),
    "rank_2": settings.PRICES.get("rank_2"),
    "rank_3": settings.PRICES.get("rank_3"),
    "rank_4": settings.PRICES.get("rank_4"),
}

DISCOUNTS = {
    "gt_6_discount": settings.PRICES.get("gt_6_discount"),
    "gt_12_discount": settings.PRICES.get("gt_12_discount"),
}


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
    try:
        period = int(post.get("period"))
    except ValueError:
        period = 0
    regions = post.getlist("regions") or post.getlist("regions[]")
    return period, regions


def new_order(request: HttpRequest) -> HttpResponse:
    """
    Saves a new order
    :param request: django.http.HttpRequest
    :return: django.http.HttpResponse
    """
    order_form = OrderForm(data=request.POST)

    if request.POST:
        if order_form.is_valid():
            order = order_form.save(commit=False)
            period, regions = get_order_data(request.POST)
            order.cost = Order.get_cost(period, regions)
            order.discount = Order.get_discount_sum(period, regions)
            order.total = order.cost - order.discount
            order.save()
            order_form.save_m2m()
            messages.add_message(
                request,
                messages.SUCCESS,
                "Спасибо! Мы получили вашу заявку и&nbsp;обработаем ее в&nbsp;ближайшее время",
            )
            capture_message("Новая заявка на расширенный доступ")

        else:
            messages.add_message(
                request,
                messages.ERROR,
                "Не удалось сохранить заявку, попробуйте позже или&nbsp;обратитесь в&nbsp;техподдержку",
            )
            capture_message(
                f"Ошибка при добавлении заявки на расширенный доступ {order_form.errors}"
            )

    return redirect("user")


def support(request: HttpRequest) -> HttpResponse:
    """
    Saves support message
    :param request: django.http.HttpRequest
    :return: django.http.HttpResponse
    """
    support_form = SupportForm(data=request.POST)

    if request.POST:
        if support_form.is_valid():
            support_form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                "Спасибо! Мы получили ваше сообщение и&nbsp;обработаем его в&nbsp;ближайшее время",
            )
            capture_message("Новое сообщение в техподдержку")

        else:
            messages.add_message(
                request,
                messages.ERROR,
                "Не удалось отправить сообщение, попробуйте позже или&nbsp;обратитесь в&nbsp;техподдержку",
            )
            capture_message(f"Ошибка при добавлении сообщения {support_form.errors}")

    return redirect(request.META["HTTP_REFERER"])


def user_profile(request: HttpRequest, code: str = None) -> HttpResponse:
    """
    User's Profile representation
    :param request: django.http.HttpRequest
    :param code: str
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
            capture_message(f"Ошибка при сохранении данных {user_form.errors}")

    return render(
        request,
        "user/user.html",
        {
            "prices": PRICES,
            "discounts": DISCOUNTS,
            "order_form": get_order_form(request.user),
            "user_form": UserForm(instance=request.user),
            "open_order": True if code else False,
            "open_regions": Region.objects.filter(rank=0),
            "code": code or request.user.region.code,
        },
    )


def get_costs(request: HttpRequest) -> JsonResponse:
    """
    Returns a JSON object with calculated
    sums of an order
    :param request: django.http.HttpRequest
    :return: int
    """
    period, regions = get_order_data(request.POST)
    return JsonResponse(
        {
            "cost": Order.get_cost(period, regions),
            "discount": Order.get_discount(period),
            "discount_sum": Order.get_discount_sum(period, regions),
        }
    )
