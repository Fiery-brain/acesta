from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import include
from django.urls import path

from acesta.stats.admin import MonitorAdmin
from acesta.stats.admin import MonitorAudienceAdmin
from acesta.stats.admin import MonitorPopularityAdmin
from acesta.stats.admin import MonitorSightsAdmin


admin.site.site_header = settings.ADMIN_TITLE
admin.site.site_title = settings.ADMIN_TITLE


urlpatterns = [
    path(
        f"{settings.ADMIN_URL}monitor/",
        staff_member_required(MonitorAdmin.as_view(template_name="admin/monitor.html")),
        name="monitor",
    ),
    path(
        f"{settings.ADMIN_URL}monitor/<str:sort>/",
        staff_member_required(MonitorAdmin.as_view(template_name="admin/monitor.html")),
        name="monitor",
    ),
    path(
        f"{settings.ADMIN_URL}monitor-sights/",
        staff_member_required(
            MonitorSightsAdmin.as_view(template_name="admin/monitor_sights.html")
        ),
        name="monitor_sights",
    ),
    path(
        f"{settings.ADMIN_URL}monitor-sights/<str:sort>/",
        staff_member_required(
            MonitorSightsAdmin.as_view(template_name="admin/monitor_sights.html")
        ),
        name="monitor_sights",
    ),
    path(
        f"{settings.ADMIN_URL}monitor-popularity/",
        staff_member_required(
            MonitorPopularityAdmin.as_view(
                template_name="admin/monitor_popularity.html"
            )
        ),
        name="monitor_popularity",
    ),
    path(
        f"{settings.ADMIN_URL}monitor-popularity/<str:sort>/",
        staff_member_required(
            MonitorPopularityAdmin.as_view(
                template_name="admin/monitor_popularity.html"
            )
        ),
        name="monitor_popularity",
    ),
    path(
        f"{settings.ADMIN_URL}monitor-audience/",
        staff_member_required(
            MonitorAudienceAdmin.as_view(template_name="admin/monitor_audience.html")
        ),
        name="monitor_audience",
    ),
    path(
        f"{settings.ADMIN_URL}monitor-audience/<str:sort>/",
        staff_member_required(
            MonitorAudienceAdmin.as_view(template_name="admin/monitor_audience.html")
        ),
        name="monitor_audience",
    ),
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("acesta.front.urls")),
    path("", include("acesta.stats.urls")),
    path("", include("acesta.user.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    # # This allows the error pages to be debugged during development, just visit
    # # these url in browser to see how these error pages look like.
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
