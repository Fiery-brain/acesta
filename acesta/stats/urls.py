from django.contrib.auth.decorators import login_required
from django.urls import include
from django.urls import path
from django.urls import re_path
from django.views.generic import TemplateView

import acesta.stats.dash  # noqa: F401
from acesta.stats.views import rating_view
from acesta.stats.views import region_view
from acesta.stats.views import set_regions_view

urlpatterns = [
    path("dashboard/", include("django_plotly_dash.urls")),
    path("dashboard/", login_required(region_view), name="region"),
    path(
        "interest/",
        login_required(TemplateView.as_view(template_name="dashboard/interest.html")),
        name="interest",
    ),
    path("rating/", login_required(rating_view), name="rating"),
    re_path(
        "rating/(?P<area>cities)/", login_required(rating_view), name="rating-cities"
    ),
    re_path(
        "rating/(?P<area>sights)/", login_required(rating_view), name="rating-sights"
    ),
    path("set_region/<str:code>/", login_required(set_regions_view), name="set_region"),
]
