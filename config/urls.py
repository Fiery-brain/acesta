from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import include
from django.urls import path

from acesta.stats.admin import MonitorAdmin


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
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("acesta.front.urls")),
    path("", include("acesta.stats.urls")),
    path("", include("acesta.user.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
