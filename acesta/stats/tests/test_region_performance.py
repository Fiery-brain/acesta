from types import SimpleNamespace
from unittest.mock import patch

from django.core.cache import caches
from django.db import connection
from django.test import override_settings
from django.test import SimpleTestCase
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from acesta.geo.models import Region
from acesta.geo.models import Sight
from acesta.geo.models import SightGroup
from acesta.stats.dash.sights_stats import update_stats_graph
from acesta.stats.helpers.sights import get_sight_groups
from acesta.stats.helpers.sights import get_sight_stats
from acesta.stats.helpers.sights import get_sights_by_group


LOCMEM_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "region-performance-default",
    },
    "db": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "region-performance-db",
    },
}


class RegionSightQueryTest(TestCase):
    def setUp(self):
        self.region = Region.objects.create(
            code="91",
            _id=9100,
            federal_district="cf",
            region="Query region",
            title="Query region",
            region_type="область",
            is_pub=True,
        )
        self.group = SightGroup.objects.create(
            name="query_group",
            title="Query group",
            title_gen="Query groups",
            tourism_type="culture",
            is_pub=True,
        )
        for index in range(3):
            sight = Sight.objects.create(
                code=self.region,
                title=f"Sight {index}",
                is_pub=True,
            )
            sight.group.add(self.group)

    def test_sight_list_relations_use_two_queries_without_n_plus_one(self):
        with CaptureQueriesContext(connection) as queries:
            sights = list(get_sights_by_group(self.region, {}))
            for sight in sights:
                str(sight.code)
                list(sight.group.all())

        self.assertEqual(len(sights), 3)
        self.assertEqual(len(queries), 2)

    def test_group_lookup_is_a_single_direct_query(self):
        with CaptureQueriesContext(connection) as queries:
            groups = list(get_sight_groups(self.region))

        self.assertEqual(groups, [self.group])
        self.assertEqual(len(queries), 1)
        self.assertNotIn(" IN (SELECT ", queries[0]["sql"].upper())


@override_settings(CACHES=LOCMEM_CACHES)
class SightStatsCacheTest(TestCase):
    def setUp(self):
        self.region = Region.objects.create(
            code="92",
            _id=9200,
            federal_district="cf",
            region="Cache region",
            title="Cache region",
            region_type="область",
            is_pub=True,
        )
        self.group = SightGroup.objects.create(
            name="cache_group",
            title="Cache group",
            title_gen="Cache groups",
            tourism_type="culture",
            is_pub=True,
        )
        sight = Sight.objects.create(
            code=self.region,
            title="Cached sight",
            is_pub=True,
        )
        sight.group.add(self.group)
        if hasattr(get_sight_stats, "_cache"):
            del get_sight_stats._cache
        caches["db"].clear()

    def tearDown(self):
        if hasattr(get_sight_stats, "_cache"):
            del get_sight_stats._cache
        super().tearDown()

    def test_warm_stats_cache_skips_aggregation_query(self):
        with CaptureQueriesContext(connection) as cold_queries:
            cold_result = get_sight_stats(code=self.region.code)
        with CaptureQueriesContext(connection) as warm_queries:
            warm_result = get_sight_stats(code=self.region.code)

        self.assertEqual(warm_result, cold_result)
        self.assertEqual(len(cold_queries), 1)
        self.assertEqual(len(warm_queries), 0)


@override_settings(
    TOURISM_TYPE_PALETTE={
        "culture": "#C84868",
        "health": "#DF8664",
    }
)
class SightStatsGraphTest(SimpleTestCase):
    request = SimpleNamespace(
        user=SimpleNamespace(current_region=SimpleNamespace(code="01")),
        COOKIES={"innerHeight": "900"},
    )
    stats = [
        {
            "name": "culture",
            "title": "культурно-познавательный туризм",
            "groups": "Музеи",
            "cnt": 12,
        },
        {
            "name": "health",
            "title": "оздоровительный туризм",
            "groups": "Санатории",
            "cnt": 5,
        },
    ]

    @patch("acesta.stats.dash.sights_stats.get_sight_stats")
    def test_graph_preserves_values_order_colors_and_tooltips(self, stats_mock):
        stats_mock.return_value = self.stats

        graph = update_stats_graph(request=self.request)
        figure = graph.figure
        trace = figure.data[0]

        self.assertEqual(list(trace.x), [12, 5])
        self.assertEqual(list(trace.y), [row["title"] for row in self.stats])
        self.assertEqual(
            list(trace.marker.color),
            ["#C84868", "#DF8664"],
        )
        self.assertEqual(list(trace.customdata), [["Музеи"], ["Санатории"]])
        self.assertEqual(
            list(figure.layout.yaxis.categoryarray),
            [row["title"] for row in reversed(self.stats)],
        )
        self.assertEqual(figure.layout.margin.t, 60)

    @patch("acesta.stats.dash.sights_stats.get_sight_stats", return_value=[])
    def test_graph_supports_region_without_sights(self, stats_mock):
        graph = update_stats_graph(request=self.request)

        self.assertEqual(list(graph.figure.data[0].x), [])
        self.assertEqual(list(graph.figure.data[0].y), [])
