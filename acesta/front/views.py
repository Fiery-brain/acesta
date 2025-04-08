import datetime
from math import ceil

from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView

from acesta.front.helpers import get_random_sight_group
from acesta.front.helpers import get_random_tourism_type
from acesta.front.helpers import get_sights_cnt
from acesta.front.helpers import get_top_regions
from acesta.front.helpers import get_top_sights
from acesta.stats.helpers.base import get_regions_cnt
from acesta.user.utils import get_support_form


def index(request: HttpRequest) -> HttpResponse:
    """
    Index page
    :param request: django.http.HttpRequest
    :return: django.http.HttpResponse
    """
    tourism_type_name, tourism_type = get_random_tourism_type()
    sight_group_name, sight_group = get_random_sight_group()

    return render(
        request,
        "index.html",
        {
            "tourism_types": settings.TOURISM_TYPES_OUTSIDE,
            "tourism_types_col_qty": str(ceil(len(settings.TOURISM_TYPES_OUTSIDE) / 2)),
            "tourism_type_name": tourism_type_name,
            "tourism_type": tourism_type,
            "sight_group_name": sight_group_name,
            "sight_group": sight_group,
            "top_regions": get_top_regions(tourism_type_name),
            "top_sights": get_top_sights(sight_group_name),
            "regions_cnt": get_regions_cnt(),
            "sights_cnt": get_sights_cnt(),
            "tourism_types_cnt": len(settings.TOURISM_TYPES_OUTSIDE),
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
        return context


sitemap = SitemapView.as_view()
