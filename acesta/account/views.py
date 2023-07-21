from allauth.account.adapter import get_adapter
from allauth.account.views import PasswordChangeView as BasePasswordChangeView
from allauth.account.views import PasswordSetView as BasePasswordSetView
from allauth.account.views import SignupView as BaseSignupView
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from acesta.account.forms import ChangeEmailForm
from acesta.geo.utils import get_geo_objects_from_geo_base
from acesta.user.utils import send_message

User = get_user_model()


class SignupView(BaseSignupView):
    def get_initial(self):
        initial = super().get_initial()
        if not initial.get("region") or not initial.get("city"):
            region, city = get_geo_objects_from_geo_base(self.request)
            if not initial.get("region") and region:
                initial["region"] = region.code
            if not initial.get("city") and city:
                initial["city"] = city.id
        return initial

    def form_valid(self, form):
        send_message("Новая регистрация через форму")
        return super().form_valid(form)

    def form_invalid(self, form):
        send_message(f"Ошибка при регистрации через форму {form.errors}")
        return super().form_invalid(form)


signup = SignupView.as_view()


class PasswordChangeView(BasePasswordChangeView):
    success_url = reverse_lazy("user")
    error_url = reverse_lazy("user")

    def form_invalid(self, form) -> HttpResponseRedirect:
        """
        Form data are not valid
        :param form: django.Form
        :return: django.http.HttpResponseRedirect
        """
        get_adapter(self.request).add_message(
            self.request,
            messages.ERROR,
            "account/messages/password_was_not_set.txt",
        )
        return redirect(self.error_url)


password_change = login_required(PasswordChangeView.as_view())


class PasswordSetView(BasePasswordSetView):
    success_url = reverse_lazy("user")
    error_url = reverse_lazy("user")

    def form_invalid(self, form) -> HttpResponseRedirect:
        """
        Form data are not valid
        :param form: django.Form
        :return: django.http.HttpResponseRedirect
        """
        get_adapter(self.request).add_message(
            self.request,
            messages.ERROR,
            "account/messages/password_was_not_changed.txt",
        )
        return redirect(self.error_url)


password_set = login_required(PasswordSetView.as_view())


class ChangeEmailView(FormView):
    model = User
    form_class = ChangeEmailForm
    success_url = reverse_lazy("user")
    error_url = reverse_lazy("user")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        get_adapter(self.request).add_message(
            self.request,
            messages.SUCCESS,
            "account/messages/email_changed.txt",
        )
        return super().form_valid(form)

    def form_invalid(self, form) -> HttpResponseRedirect:
        """
        Form data are not valid
        :param form: django.Form
        :return: django.http.HttpResponseRedirect
        """
        get_adapter(self.request).add_message(
            self.request,
            messages.ERROR,
            "account/messages/email_was_not_changed.txt",
        )
        return redirect(self.error_url)


email_change = login_required(ChangeEmailView.as_view())
