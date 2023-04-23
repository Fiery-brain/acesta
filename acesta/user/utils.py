from acesta.user.forms import OrderForm
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


def get_order_form(user: User) -> OrderForm:
    """
    Returns Order Form
    :param user: User
    :return: OrderForm
    """
    order_form = OrderForm()
    order_form.initial["period"] = 6
    order_form.initial["user"] = user
    user_field = order_form.fields["user"]
    user_field.widget = user_field.hidden_widget()
    return order_form
