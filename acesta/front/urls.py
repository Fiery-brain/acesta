from django.urls import path
from django.urls import re_path
from django.views.generic import TemplateView

from acesta.front.utils import get_segment_pattern
from acesta.front.views import help
from acesta.front.views import landing_hub
from acesta.front.views import segment_landing
from acesta.front.views import sitemap

urlpatterns = [
    path("terms/", TemplateView.as_view(template_name="terms.html"), name="terms"),
    path(
        "privacy/", TemplateView.as_view(template_name="privacy.html"), name="privacy"
    ),
    path("help/", help, name="help"),
    path("sitemap.xml", sitemap, name="sitemap"),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots",
    ),
    re_path(
        rf"^(?P<segment>{get_segment_pattern()})/",
        segment_landing,
        name="segment_index",
    ),
    path("", landing_hub, name="index"),
]
