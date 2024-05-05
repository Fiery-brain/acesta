from allauth.account import app_settings
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
from acesta.account.forms import SignupNextForm
from acesta.geo.utils import get_geo_objects_from_geo_base
from acesta.user.utils import send_message

User = get_user_model()


class SignupView(BaseSignupView):
    is_time_check = None
    success_url = reverse_lazy("account_signupnext")

    def get_is_time_check(self):
        if self.is_time_check is None:
            try:
                self.is_time_check = bool(
                    int(self.request.POST.get("time_checker", default=False))
                )
            except ValueError:
                self.is_time_check = False
        return self.is_time_check

    def dispatch(self, request, *args, **kwargs):
        return super(FormView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if self.get_is_time_check() and form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        send_message("Новая регистрация через форму")
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.get_is_time_check():
            send_message(f"Ошибка при регистрации через форму {form.errors}")
        elif form.is_valid():
            get_adapter(self.request).add_message(
                self.request,
                messages.ERROR,
                "account/messages/too_many_registration_requests.txt",
            )
        return super().form_invalid(form)


signup = SignupView.as_view()


class SignupnextView(FormView):
    template_name = "account/signupnext." + app_settings.TEMPLATE_EXTENSION
    success_url = reverse_lazy("region")
    form_class = SignupNextForm

    def get_initial(self):
        initial = super().get_initial()
        if not initial.get("region"):
            region, _ = get_geo_objects_from_geo_base(self.request)
            if not initial.get("region") and region:
                initial["region"] = region.code
        return initial

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.registered:
            response = HttpResponseRedirect(self.success_url)
        else:
            response = super(FormView, self).dispatch(request, *args, **kwargs)
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        data = form.cleaned_data
        self.request.user.region = data.get("region")
        self.request.user.current_region = data.get("region")
        self.request.user.purpose = data.get("purpose")
        self.request.user.subscription = data.get("subscription", True)
        self.request.user.registered = True
        self.request.user.set_password(data.get("password1"))
        self.request.user.save(
            update_fields=[
                "region",
                "current_region",
                "registered",
                "purpose",
                "subscription",
                "password",
            ]
        )
        get_adapter().login(self.request, self.request.user)
        send_message("Новый вход после регистрации")
        return super().form_valid(form)

    def form_invalid(self, form):
        send_message(f"Ошибка входа после регистрации {form.errors}")
        return super().form_invalid(form)


signupnext = SignupnextView.as_view()


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
