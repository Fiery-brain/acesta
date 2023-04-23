from django.urls import path
from django.views.generic import TemplateView

from acesta.front.views import help
from acesta.front.views import index

urlpatterns = [
    path("terms/", TemplateView.as_view(template_name="terms.html"), name="terms"),
    path(
        "privacy/", TemplateView.as_view(template_name="privacy.html"), name="privacy"
    ),
    path("help/", help, name="help"),
    path("", index, name="index"),
]
