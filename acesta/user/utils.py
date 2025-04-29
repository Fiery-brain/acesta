import os

from django.conf import settings
from django.core.mail import mail_admins

from acesta.user.forms import OrderForm
from acesta.user.forms import RequestForm
from acesta.user.forms import SupportForm
from acesta.user.models import User


def get_support_form(user: User, subject: str) -> SupportForm:
    """
    Returns Support Form
    :param user: User
    :param subject: str
    :return: SupportForm
    """
    support_form = SupportForm()
    support_form.initial["subject"] = subject
    support_form.initial["user"] = user
    subject_field = support_form.fields["subject"]
    subject_field.widget = subject_field.hidden_widget()
    user_field = support_form.fields["user"]
    user_field.widget = user_field.hidden_widget()
    return support_form


def get_request_form(user: User, subject: str) -> RequestForm:
    """
    Returns Request Form
    :param user: User
    :param subject: str
    :return: RequestForm
    """
    request_form = RequestForm()
    request_form.initial["subject"] = subject
    if user.is_authenticated:
        request_form.initial["user"] = user
    subject_field = request_form.fields["subject"]
    subject_field.widget = subject_field.hidden_widget()
    user_field = request_form.fields["user"]
    user_field.widget = user_field.hidden_widget()
    return request_form


def get_order_form(user: User) -> OrderForm:
    """
    Returns Order Form
    :param user: User
    :return: OrderForm
    """
    order_form = OrderForm()
    order_form.initial["period"] = 0.25
    order_form.initial["user"] = user
    order_form.initial["tourism_types"] = ["recreation"]
    user_field = order_form.fields["user"]
    user_field.widget = user_field.hidden_widget()
    return order_form


def fetch_pdf_resources(uri: str, rel: str) -> str:
    """
    Adds the additional paths for pdf rendering
    :param uri: str
    :param rel: str
    :return: str
    """
    if uri.find(settings.MEDIA_URL) != -1:
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.find(settings.STATIC_URL) != -1:
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    else:
        path = None
    return path


def send_message(message) -> None:
    """
    Captures a message
    :return: None
    """
    if not settings.TESTING:
        return mail_admins(message.replace("\n", " "), message)
