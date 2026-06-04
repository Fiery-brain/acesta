from django.conf import settings
from django.urls import path
from django.urls import re_path
from django.views.generic import TemplateView

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
        rf"^(?P<segment>{settings.SEGMENT_GOVERNMENT}"
        rf"|{settings.SEGMENT_TIC}"
        rf"|{settings.SEGMENT_TOUR_OPERATOR}"
        rf"|{settings.SEGMENT_TOUR_AGENT}"
        rf"|{settings.SEGMENT_TOURISM_PRODUCT_OWNER}"
        rf"|{settings.SEGMENT_INVESTORS}"
        rf"|{settings.SEGMENT_GUIDE}"
        rf"|{settings.SEGMENT_MARKETING_AGENCY}"
        rf"|{settings.SEGMENT_HOSPITALITY}"
        rf"|{settings.SEGMENT_TOURISM_EVENT}"
        rf"|{settings.SEGMENT_TRANSPORTATION})/",
        segment_landing,
        name="segment_index",
    ),
    path("", landing_hub, name="index"),
]
