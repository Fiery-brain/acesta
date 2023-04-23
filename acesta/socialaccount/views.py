from allauth.socialaccount.views import ConnectionsView as BaseConnectionsView
from allauth.socialaccount.views import SignupView as BaseSignupView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from sentry_sdk import capture_message

from acesta.geo.utils import get_geo_objects_from_geo_base


class SignupView(BaseSignupView):
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not form.initial.get("region") or not form.initial.get("city"):
            region, city = get_geo_objects_from_geo_base(self.request)
            if not form.initial.get("region") and region:
                form.fields["region"].initial = region
            if not form.initial.get("city") and city:
                form.initial["city"] = city
        return form

    def form_valid(self, form):
        capture_message("Новая регистрация через соцсеть")
        return super().form_valid(form)


social_signup = SignupView.as_view()


class ConnectionsView(BaseConnectionsView):
    success_url = reverse_lazy("user")


connections = login_required(ConnectionsView.as_view())
