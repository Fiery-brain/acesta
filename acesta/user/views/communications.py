from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import FileResponse
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone

from acesta.user.forms import RequestForm
from acesta.user.forms import SupportForm
from acesta.user.utils import send_message


def visitor_request(request: HttpRequest) -> HttpResponse or FileResponse:
    """
    Saves request
    :param request: django.http.HttpRequest
    :return: django.http.HttpResponse
    """
    if request.method == "POST":
        is_consultation = request.POST["subject"] == settings.REQUEST_CONSULTATION

        data = request.POST.copy()

        if is_consultation:
            data["time"] = timezone.now() + relativedelta(minutes=60)
        request_form = RequestForm(data=data)

        try:
            is_time_check = bool(int(request.POST.get("time_checker", default=False)))
        except ValueError:
            is_time_check = False

        if is_time_check and request_form.is_valid() and request.user.is_authenticated:
            request_form.save()
            if is_consultation:
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    "Спасибо! Мы получили запрос и&nbsp;свяжемся с вами в ближайшее время",
                )
            try:
                send_mail(
                    f"Новый запрос {'консультации' if is_consultation else 'презентации'}",
                    f"""Новый запрос {'консультации' if is_consultation else 'презентации'}
                        {request.POST['name']}
                        {request.POST['channel']} {request.POST['_id']} {request.POST['comment']}""",
                    settings.DEFAULT_FROM_EMAIL,
                    settings.ADMINS,
                    fail_silently=False,
                )
            except RuntimeError:
                send_message("Новый запрос посетителя")

        else:
            messages.add_message(
                request,
                messages.ERROR,
                "Не удалось отправить запрос, попробуйте позже или&nbsp;обратитесь в&nbsp;техподдержку",
            )
            if is_time_check:
                send_message(f"Ошибка при добавлении сообщения {request_form.errors}")

        if request.POST["subject"] == settings.REQUEST_PRESENTATION and is_time_check:
            return FileResponse(
                open(
                    f'{str(settings.APPS_DIR / "templates")}/Tourism-analytics-acesta-presentation.pdf',
                    "rb",
                ),
                content_type="application/pdf",
            )
        else:
            return redirect(request.META["HTTP_REFERER"])

    else:
        return redirect("index")


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
                "Спасибо! Мы получили сообщение и&nbsp;обработаем его в&nbsp;ближайшее время",
            )
            send_message("Новое сообщение в техподдержку")

        else:
            messages.add_message(
                request,
                messages.ERROR,
                "Не удалось отправить сообщение, попробуйте позже или&nbsp;обратитесь в&nbsp;техподдержку",
            )
            send_message(f"Ошибка при добавлении сообщения {support_form.errors}")

    return redirect(request.META["HTTP_REFERER"])
