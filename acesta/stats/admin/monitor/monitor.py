import environ
from django.db import models
from django.views.generic import TemplateView
from Levenshtein import ratio

from acesta.geo.models import Sight
from acesta.stats.admin.monitor.audience import get_audience_monitor
from acesta.stats.admin.monitor.popularity import get_ppt_monitor
from acesta.stats.admin.monitor.popularity import get_suspicious_queries
from acesta.stats.admin.monitor.sights import get_sights_monitor
from acesta.stats.admin.monitor.sights import get_suspicious_kernels

env = environ.Env()


class MonitorAdmin(TemplateView):
    def get(self, request, *args, **kwargs):
        queries_data = [
            (
                sight.get("code"),
                sight.get("qt"),
                sum([v for k, v in sight.get("kernel")[:3]]),
                sight.get("code__title"),
                sight.get("id"),
                sight.get("title"),
                sight.get("query"),
                sight.get("query_additional"),
                sight.get("kernel"),
                ratio(sight.get("query"), sight.get("kernel")[0][0])
                if len(sight.get("kernel"))
                else 1,
                ratio(sight.get("query_additional"), sight.get("kernel")[0][0])
                if len(sight.get("kernel"))
                else 1,
            )
            for sight in (
                Sight.objects.annotate(
                    qt=models.Sum("sight_all_region_popularity__qty")
                )
                .filter(is_checked=True, is_pub=True)
                .values(
                    "code",
                    "qt",
                    "kernel",
                    "code__title",
                    "id",
                    "title",
                    "query",
                    "query_additional",
                )
            ).order_by("code")
        ]

        context = self.get_context_data(**kwargs)
        context.update(
            dict(
                title="Монитор",
                sights=get_sights_monitor(self.kwargs),
                suspicious_kernels=get_suspicious_kernels(queries_data, self.kwargs),
                suspicious_queries=get_suspicious_queries(queries_data, self.kwargs),
                ppt=get_ppt_monitor(queries_data, self.kwargs),
                audience=get_audience_monitor(self.kwargs),
            )
        )
        return self.render_to_response(context)
