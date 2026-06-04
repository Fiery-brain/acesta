import datetime

from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView

from acesta.front.segment_settings import SECTION_FEATURES
from acesta.front.segment_settings import SECTION_HASH_TAGS
from acesta.front.segment_settings import SECTION_HERO
from acesta.front.segment_settings import SECTION_PAGE_META
from acesta.front.segment_settings import SECTION_WORKFLOW
from acesta.front.segment_settings import SECTION_YOUR_SCENARIO
from acesta.front.segment_settings import SECTION_YOUR_SEGMENT
from acesta.front.segment_settings import SEGMENT_CONFIG
from acesta.user.utils import get_support_form


def landing_hub(request: HttpRequest) -> HttpResponse:
    """
    Landing Hub page
    :param request: django.http.HttpRequest
    :return: django.http.HttpResponse
    """
    return render(
        request,
        "landing_hub.html",
        {
            "segment_name": settings.DEFAULT_SEGMENT,
            "PAGE_META": SEGMENT_CONFIG[SECTION_PAGE_META].get(
                settings.DEFAULT_SEGMENT
            ),
            "HERO": SEGMENT_CONFIG[SECTION_HERO].get(settings.DEFAULT_SEGMENT),
            "YOUR_SEGMENT": SEGMENT_CONFIG[SECTION_YOUR_SEGMENT],
            "YOUR_SCENARIO": SEGMENT_CONFIG[SECTION_YOUR_SCENARIO],
        },
    )


def segment_landing(
    request: HttpRequest, segment: str = settings.DEFAULT_SEGMENT
) -> HttpResponse:
    """
    Segment Landing page
    :param request: django.http.HttpRequest
    :param segment: str
    :return: django.http.HttpResponse
    """
    request.session["current_segment"] = segment
    return render(
        request,
        "segment_landing.html",
        {
            "segment_name": segment,
            "SEGMENT_HASH_TAGS": SEGMENT_CONFIG[SECTION_HASH_TAGS].get(segment),
            "PAGE_META": SEGMENT_CONFIG[SECTION_PAGE_META].get(segment),
            "HERO": SEGMENT_CONFIG[SECTION_HERO].get(segment),
            "FEATURES": SEGMENT_CONFIG[SECTION_FEATURES].get(segment),
            "WORKFLOW": SEGMENT_CONFIG[SECTION_WORKFLOW].get(segment),
        },
    )


def help(request: HttpRequest) -> HttpResponse:
    """
    Help page
    :param request: django.http.HttpRequest
    :return: django.http.HttpResponse
    """
    return render(
        request,
        "help.html",
        {
            "support_form": get_support_form(request.user, settings.SUPPORT_QUESTION),
        },
    )


class SitemapView(TemplateView):
    """
    Sitemap View
    """

    template_name = "sitemap.xml"
    content_type = "text/xml"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["now"] = timezone.now()
        context["week_ago"] = timezone.now() - datetime.timedelta(days=7)
        context["segment_pages"] = (
            settings.SEGMENT_GOVERNMENT,
            settings.SEGMENT_TIC,
            settings.SEGMENT_TOUR_OPERATOR,
            settings.SEGMENT_TOUR_AGENT,
            settings.SEGMENT_TOURISM_PRODUCT_OWNER,
            settings.SEGMENT_INVESTORS,
            settings.SEGMENT_GUIDE,
            settings.SEGMENT_MARKETING_AGENCY,
            settings.SEGMENT_HOSPITALITY,
            settings.SEGMENT_TOURISM_EVENT,
            settings.SEGMENT_TRANSPORTATION,
        )
        return context


sitemap = SitemapView.as_view()
