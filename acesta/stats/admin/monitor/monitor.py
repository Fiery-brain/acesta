import environ
from django.views.generic import TemplateView

from acesta.stats.admin.monitor.audience import get_audience_monitor
from acesta.stats.admin.monitor.popularity import get_ppt_monitor
from acesta.stats.admin.monitor.popularity import get_suspicious_queries
from acesta.stats.admin.monitor.sights import get_sights
from acesta.stats.admin.monitor.sights import get_sights_monitor
from acesta.stats.admin.monitor.sights import get_suspicious_kernels

env = environ.Env()


class MonitorAdmin(TemplateView):
    pass


class MonitorSightsAdmin(TemplateView):
    def get(self, request, *args, **kwargs):
        sights = get_sights()
        context = self.get_context_data(**kwargs)
        context.update(
            dict(
                title="Точки притяжения",
                is_nav_sidebar_enabled=True,
                sights=get_sights_monitor(self.kwargs),
                suspicious_kernels=get_suspicious_kernels(sights, self.kwargs),
                audience=get_audience_monitor(self.kwargs),
            )
        )
        return self.render_to_response(context)


class MonitorPopularityAdmin(TemplateView):
    def get(self, request, *args, **kwargs):
        sights = get_sights()
        context = self.get_context_data(**kwargs)
        context.update(
            dict(
                title="Популярность",
                is_nav_sidebar_enabled=True,
                suspicious_queries=get_suspicious_queries(sights, self.kwargs),
                ppt=get_ppt_monitor(sights, self.kwargs),
            )
        )
        return self.render_to_response(context)


class MonitorAudienceAdmin(TemplateView):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update(
            dict(
                title="Аудитория",
                is_nav_sidebar_enabled=True,
                audience=get_audience_monitor(self.kwargs),
            )
        )
        return self.render_to_response(context)
