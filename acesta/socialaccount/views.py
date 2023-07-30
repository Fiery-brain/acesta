from allauth.socialaccount.views import ConnectionsView as BaseConnectionsView
from allauth.socialaccount.views import SignupView as BaseSignupView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

from acesta.user.utils import send_message


class SignupView(BaseSignupView):
    success_url = reverse_lazy("account_signupnext")

    def form_valid(self, form):
        send_message("Новая регистрация через соцсеть")
        return super().form_valid(form)

    def form_invalid(self, form):
        send_message(f"Ошибка при регистрации через соцсеть {form.errors}")
        return super().form_invalid(form)


social_signup = SignupView.as_view()


class ConnectionsView(BaseConnectionsView):
    success_url = reverse_lazy("user")


connections = login_required(ConnectionsView.as_view())
