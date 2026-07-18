from datetime import date
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from django.test import SimpleTestCase

from acesta.stats.history import _forecast
from acesta.stats.history import _impute
from acesta.stats.history import _normalized_place_values
from acesta.stats.history import _render_history_header
from acesta.stats.history import _series
from acesta.stats.models.abstract import AudienceHistoryMixin
from acesta.stats.models.abstract import HistoryMixin
from acesta.stats.models.abstract import PopularityHistoryMixin
from acesta.stats.models.abstract import RatingHistoryMixin


class HistoryChartStyleTest(SimpleTestCase):
    def test_actual_markers_are_filled_and_forecast_markers_stay_outlined(self):
        script = (
            Path(__file__).resolve().parents[2] / "static/js/dashboard.history.js"
        ).read_text()
        actual_trace = script.split("function buildTraces", 1)[1].split(
            "if (forecast.length)", 1
        )[0]
        forecast_traces = script.split("if (forecast.length)", 1)[1]

        self.assertIn("marker: { color: color, size: 8 }", actual_trace)
        self.assertNotIn('color: "#ffffff"', actual_trace)
        self.assertIn(
            'marker: { color: "#ffffff", size: 8, '
            "line: { color: color, width: 2 } }",
            forecast_traces,
        )


class HistoryCalculationTest(SimpleTestCase):
    class RatingRecord:
        def __init__(self, history, modified, place, value):
            self.history = history
            self.modified = modified
            self.place = place
            self.value = value

        @staticmethod
        def _normalize_history_date(value):
            return (
                datetime.fromisoformat(value).date()
                if isinstance(value, str)
                else value
            )

    def test_imputation_is_stable_and_marked(self):
        values = {
            datetime(2024, 3, 1).date(): 100,
            datetime(2025, 3, 1).date(): 120,
        }
        target = datetime(2026, 3, 1).date()

        first = _impute(values, target, target, True)
        second = _impute(values, target, target, True)

        self.assertEqual(first, second)
        self.assertTrue(first[target]["is_imputed"])
        self.assertEqual(first[target]["value"], 110)

    def test_imputation_leaves_gap_without_seasonal_value(self):
        target = datetime(2026, 3, 1).date()

        self.assertEqual(_impute({}, target, target, True), {})

    def test_imputation_interpolates_between_neighboring_months(self):
        values = {
            datetime(2026, 1, 1).date(): 10,
            datetime(2026, 4, 1).date(): 40,
        }

        result = _impute(
            values,
            datetime(2026, 2, 1).date(),
            datetime(2026, 3, 1).date(),
            True,
        )

        self.assertEqual(result[datetime(2026, 2, 1).date()]["value"], 20)
        self.assertEqual(result[datetime(2026, 3, 1).date()]["value"], 30)
        self.assertTrue(result[datetime(2026, 2, 1).date()]["is_imputed"])
        self.assertTrue(result[datetime(2026, 3, 1).date()]["is_imputed"])

    def test_forecast_returns_two_stable_bounded_points(self):
        values = {
            datetime(2024, 7, 1).date(): 100,
            datetime(2024, 8, 1).date(): 110,
            datetime(2025, 7, 1).date(): 120,
            datetime(2025, 8, 1).date(): 130,
            datetime(2026, 5, 1).date(): 135,
            datetime(2026, 6, 1).date(): 140,
        }
        end = datetime(2026, 6, 1).date()

        forecast = _forecast(values, end, True)

        self.assertEqual(len(forecast), 2)
        self.assertEqual(forecast[0]["date"], "2026-07-01")
        self.assertEqual(forecast[1]["date"], "2026-08-01")
        self.assertTrue(all(point["is_forecast"] for point in forecast))
        self.assertGreaterEqual(forecast[0]["value"], 88)
        self.assertLessEqual(forecast[0]["value"], 132)

    def test_forecast_requires_three_actual_months(self):
        values = {
            datetime(2026, 5, 1).date(): 100,
            datetime(2026, 6, 1).date(): 110,
        }

        self.assertEqual(_forecast(values, datetime(2026, 6, 1).date(), True), [])

    def test_place_normalization_interpolates_internal_inactive_month(self):
        record = self.RatingRecord(
            history=[
                {"date": "2023-03-12", "place": 6, "value": 100},
                {"date": "2023-04-18", "place": 11492, "value": 0},
                {"date": "2023-05-16", "place": 8, "value": 100},
            ],
            modified=datetime(2023, 5, 16),
            place=8,
            value=100,
        )

        values, interpolated, blocked, forecast_end = _normalized_place_values(record)

        april = datetime(2023, 4, 1).date()
        self.assertEqual(values[april], 7)
        self.assertEqual(interpolated, {april})
        self.assertEqual(blocked, set())
        self.assertEqual(forecast_end, datetime(2023, 5, 1).date())

    def test_place_normalization_interpolates_consecutive_months_by_distance(self):
        record = self.RatingRecord(
            history=[
                {"date": "2025-01-10", "place": 10, "value": 100},
                {"date": "2025-02-10", "place": 999, "value": 0},
                {"date": "2025-03-10", "place": 999, "value": 0},
                {"date": "2025-04-10", "place": 40, "value": 100},
            ],
            modified=datetime(2025, 4, 10),
            place=40,
            value=100,
        )

        values, interpolated, _, _ = _normalized_place_values(record)

        self.assertEqual(values[datetime(2025, 2, 1).date()], 20)
        self.assertEqual(values[datetime(2025, 3, 1).date()], 30)
        self.assertEqual(
            interpolated,
            {datetime(2025, 2, 1).date(), datetime(2025, 3, 1).date()},
        )

    def test_region_place_gap_stays_inside_maximum(self):
        record = self.RatingRecord(
            history=[{"date": "2025-05-10", "place": 89, "value": 100}],
            modified=datetime(2025, 7, 10),
            place=89,
            value=100,
        )

        values, interpolated, _, _ = _normalized_place_values(record, maximum=89)

        june = datetime(2025, 6, 1).date()
        self.assertEqual(values[june], 89)
        self.assertEqual(interpolated, {june})

    def test_place_normalization_excludes_and_blocks_edge_tails(self):
        record = self.RatingRecord(
            history=[
                {"date": "2024-01-10", "place": 500, "value": 0},
                {"date": "2024-02-10", "place": 50, "value": 100},
                {"date": "2024-03-10", "place": 5, "value": 100},
                {"date": "2024-04-10", "place": 500, "value": 0},
            ],
            modified=datetime(2024, 5, 10),
            place=500,
            value=0,
        )

        values, _, blocked, forecast_end = _normalized_place_values(record)
        displayed = _impute(
            values,
            datetime(2024, 1, 1).date(),
            datetime(2024, 5, 1).date(),
            True,
            blocked,
        )

        self.assertEqual(
            set(values),
            {datetime(2024, 2, 1).date(), datetime(2024, 3, 1).date()},
        )
        self.assertEqual(
            blocked,
            {
                datetime(2024, 1, 1).date(),
                datetime(2024, 4, 1).date(),
                datetime(2024, 5, 1).date(),
            },
        )
        self.assertNotIn(datetime(2024, 4, 1).date(), displayed)
        self.assertNotIn(datetime(2024, 5, 1).date(), displayed)
        self.assertEqual(forecast_end, datetime(2024, 3, 1).date())

    def test_place_normalization_preserves_large_active_jump(self):
        record = self.RatingRecord(
            history=[
                {"date": "2025-01-10", "place": 70, "value": 10},
                {"date": "2025-02-10", "place": 25, "value": 20},
            ],
            modified=datetime(2025, 2, 10),
            place=25,
            value=20,
        )

        values, interpolated, _, _ = _normalized_place_values(record)

        self.assertEqual(
            values,
            {
                datetime(2025, 1, 1).date(): 70,
                datetime(2025, 2, 1).date(): 25,
            },
        )
        self.assertEqual(interpolated, set())

    def test_place_series_marks_interpolation_and_forecasts_from_last_active_month(
        self,
    ):
        record = self.RatingRecord(
            history=[
                {"date": "2025-01-10", "place": 10, "value": 100},
                {"date": "2025-02-10", "place": 999, "value": 0},
                {"date": "2025-03-10", "place": 30, "value": 100},
                {"date": "2025-04-10", "place": 40, "value": 100},
                {"date": "2025-05-10", "place": 999, "value": 0},
            ],
            modified=datetime(2025, 6, 10),
            place=999,
            value=0,
        )
        specs = [
            {
                "id": "place",
                "name": "Место",
                "history_key": "place",
                "current_key": "place",
                "unit": "",
                "axis": "y",
                "integer": True,
            }
        ]

        result = _series(record, specs)[0]
        points = {point["date"]: point for point in result["points"]}

        self.assertEqual(points["2025-02-01"]["value"], 20)
        self.assertTrue(points["2025-02-01"]["is_imputed"])
        self.assertNotIn("2025-05-01", points)
        self.assertNotIn("2025-06-01", points)
        self.assertEqual(result["forecast"][0]["date"], "2025-05-01")
        self.assertEqual(result["forecast"][1]["date"], "2025-06-01")

    def test_region_place_history_and_forecast_respect_maximum(self):
        record = self.RatingRecord(
            history=[
                {"date": "2024-06-10", "place": 89, "value": 100},
                {"date": "2025-05-10", "place": 89, "value": 100},
                {"date": "2025-07-10", "place": 89, "value": 100},
            ],
            modified=datetime(2026, 5, 10),
            place=89,
            value=100,
        )
        specs = [
            {
                "id": "place",
                "name": "Место",
                "history_key": "place",
                "current_key": "place",
                "unit": "",
                "axis": "y",
                "integer": True,
                "maximum": 89,
            }
        ]

        result = _series(record, specs)[0]

        self.assertTrue(all(point["value"] <= 89 for point in result["points"]))
        self.assertTrue(all(point["value"] <= 89 for point in result["forecast"]))

    def test_dyatlov_pass_outlier_is_normalized_before_forecast(self):
        history = [
            {"date": "2023-03-12", "place": 6, "value": 574085},
            {"date": "2023-04-18", "place": 11492, "value": 0},
            {"date": "2023-05-16", "place": 8, "value": 414656},
            {"date": "2024-04-13", "place": 10, "value": 492265},
            {"date": "2025-04-18", "place": 6, "value": 523800},
            {"date": "2025-09-18", "place": 7, "value": 487941},
            {"date": "2025-10-22", "place": 6, "value": 710299},
            {"date": "2025-11-19", "place": 6, "value": 585326},
            {"date": "2025-12-23", "place": 6, "value": 652370},
            {"date": "2026-01-20", "place": 1, "value": 1530518},
        ]
        record = self.RatingRecord(
            history=history,
            modified=datetime(2026, 2, 16),
            place=3,
            value=841432,
        )
        specs = [
            {
                "id": "place",
                "name": "Место",
                "history_key": "place",
                "current_key": "place",
                "unit": "",
                "axis": "y",
                "integer": True,
            }
        ]

        result = _series(record, specs)[0]

        self.assertEqual(result["forecast"][0]["date"], "2026-03-01")
        self.assertEqual(result["forecast"][1]["date"], "2026-04-01")
        self.assertLess(result["forecast"][1]["value"], 100)
        self.assertNotEqual(result["forecast"][1]["value"], 1537)

    def test_series_does_not_mutate_history(self):
        class PopularityRecord:
            modified = datetime(2026, 6, 20)
            qty = 140
            history = [
                {"date": "2025-06-20", "qty": 100},
                {"date": "2026-04-20", "qty": 120},
                {"date": "2026-05-20", "qty": 130},
            ]

            @staticmethod
            def _normalize_history_date(value):
                return (
                    datetime.fromisoformat(value).date()
                    if isinstance(value, str)
                    else value
                )

        record = PopularityRecord()
        original = [item.copy() for item in record.history]
        specs = [
            {
                "id": "qty",
                "name": "Запросы",
                "history_key": "qty",
                "current_key": "qty",
                "unit": "",
                "axis": "y",
                "integer": True,
            }
        ]

        result = _series(record, specs)

        self.assertEqual(record.history, original)
        self.assertEqual(result[0]["points"][-1]["value"], 140)


class HistorySnapshotTest(SimpleTestCase):
    class BaseRecord:
        history_fields = None
        history = []
        date = datetime(2026, 7, 14)
        modified = datetime(2026, 7, 15)

        _normalize_history_date = staticmethod(HistoryMixin._normalize_history_date)
        _get_history_snapshot_date = HistoryMixin._get_history_snapshot_date
        _history_without_snapshot_month = HistoryMixin._history_without_snapshot_month
        _add_history_snapshot = HistoryMixin._add_history_snapshot
        add_history = HistoryMixin.add_history
        rollback_previous_month = HistoryMixin.rollback_previous_month

    class PopularityRecord(BaseRecord):
        history_fields = PopularityHistoryMixin.history_fields
        qty = 10
        popularity_mean_all = 21.5
        popularity_mean = 20.5
        popularity_max = 99.0

    class RatingRecord(BaseRecord):
        history_fields = RatingHistoryMixin.history_fields
        value = 30
        place = 2

    class AudienceRecord(BaseRecord):
        history_fields = AudienceHistoryMixin.history_fields
        v_all = 100
        v_types = 90
        v_type_sex_age = 80
        v_sex_age = 70
        v_sex_age_child_6 = 60
        v_sex_age_child_7_12 = 50
        v_sex_age_parents = 40
        v_type_in_pair = 30
        coeff = 1.25

    def get_record(self, record_class):
        record = record_class()
        record.history = []
        return record

    def test_snapshot_uses_current_values_before_update(self):
        record = self.get_record(self.BaseRecord)
        record.qty = 10
        record.popularity_mean = 20.5

        record._add_history_snapshot({"qty": "qty", "mean": "popularity_mean"})
        record.qty = 99
        record.popularity_mean = 199.5

        self.assertEqual(
            record.history[0],
            {"date": "2026-07-14", "qty": 10, "mean": 20.5},
        )

    def test_snapshot_replaces_existing_item_in_same_month(self):
        record = self.get_record(self.BaseRecord)
        record.qty = 10
        record.history = [
            {"date": "2026-07-01", "qty": 1},
            {"date": "2026-06-30", "qty": 2},
        ]

        record._add_history_snapshot(["qty"])

        self.assertEqual(
            record.history,
            [
                {"date": "2026-07-14", "qty": 10},
                {"date": "2026-06-30", "qty": 2},
            ],
        )

    def test_history_without_snapshot_month_preserves_other_and_invalid_dates(self):
        record = self.get_record(self.BaseRecord)
        history = [
            {"date": "2026-07-01", "qty": 1},
            {"date": "2026-07-31", "qty": 2},
            {"date": "2026-06-30", "qty": 3},
            {"date": "broken", "qty": 4},
            {"qty": 5},
        ]

        filtered = record._history_without_snapshot_month(
            history,
            datetime(2026, 7, 14).date(),
        )

        self.assertEqual(
            filtered,
            [
                {"date": "2026-06-30", "qty": 3},
                {"date": "broken", "qty": 4},
                {"qty": 5},
            ],
        )

    def test_popularity_history_uses_popularity_payload(self):
        record = self.get_record(self.PopularityRecord)

        record.add_history()

        self.assertEqual(
            record.history[0],
            {
                "date": "2026-07-14",
                "qty": 10,
                "mean_all": 21.5,
                "mean": 20.5,
                "max": 99.0,
            },
        )

    def test_rating_history_uses_rating_payload(self):
        record = self.get_record(self.RatingRecord)

        record.add_history()

        self.assertEqual(
            record.history[0],
            {"date": "2026-07-14", "value": 30, "place": 2},
        )

    def test_audience_history_uses_audience_payload(self):
        record = self.get_record(self.AudienceRecord)

        record.add_history()

        self.assertEqual(
            record.history[0],
            {
                "date": "2026-07-14",
                "v_all": 100,
                "v_types": 90,
                "v_type_sex_age": 80,
                "v_sex_age": 70,
                "v_sex_age_child_6": 60,
                "v_sex_age_child_7_12": 50,
                "v_sex_age_parents": 40,
                "v_type_in_pair": 30,
                "coeff": 1.25,
            },
        )

    def test_base_history_requires_history_fields(self):
        record = self.get_record(self.BaseRecord)

        with self.assertRaisesMessage(
            NotImplementedError,
            "BaseRecord must define history_fields.",
        ):
            record.add_history()

    def test_rollback_previous_month_restores_dict_fields_and_consumes_snapshot(self):
        record = self.get_record(self.PopularityRecord)
        record.qty = 99
        record.popularity_mean_all = 98
        record.popularity_mean = 97
        record.popularity_max = 96
        record.history = [
            {
                "date": "2026-06-18",
                "qty": 10,
                "mean_all": 20,
                "mean": 30,
                "max": 40,
            },
            {"date": "2026-05-18", "qty": 1},
        ]

        restored = record.rollback_previous_month(date(2026, 7, 15))

        self.assertTrue(restored)
        self.assertEqual(record.qty, 10)
        self.assertEqual(record.popularity_mean_all, 20)
        self.assertEqual(record.popularity_mean, 30)
        self.assertEqual(record.popularity_max, 40)
        self.assertEqual(record.date.date(), date(2026, 6, 18))
        self.assertEqual(record.modified.date(), date(2026, 6, 18))
        self.assertEqual(record.history, [{"date": "2026-05-18", "qty": 1}])

    def test_rollback_previous_month_supports_list_fields(self):
        record = self.get_record(self.RatingRecord)
        record.value = 99
        record.place = 9
        record.history = [{"date": "2026-06-30", "value": 30, "place": 2}]

        self.assertTrue(record.rollback_previous_month(date(2026, 7, 1)))
        self.assertEqual((record.value, record.place), (30, 2))
        self.assertEqual(record.history, [])

    def test_rollback_previous_month_does_not_use_older_or_partial_snapshot(self):
        record = self.get_record(self.RatingRecord)
        original = [
            {"date": "broken", "value": 10, "place": 1},
            {"date": "2026-06-10", "value": 20},
            {"date": "2026-05-10", "value": 30, "place": 3},
        ]
        record.history = list(original)

        self.assertFalse(record.rollback_previous_month(date(2026, 7, 15)))
        self.assertEqual(record.history, original)

    def test_rollback_previous_month_is_idempotent_for_same_fill_date(self):
        record = self.get_record(self.RatingRecord)
        record.history = [
            {"date": "2026-06-10", "value": 20, "place": 2},
            {"date": "2026-05-10", "value": 10, "place": 1},
        ]

        self.assertTrue(record.rollback_previous_month(date(2026, 7, 15)))
        self.assertFalse(record.rollback_previous_month(date(2026, 7, 15)))
        self.assertEqual((record.value, record.place), (20, 2))


class NamedEntity:
    def __init__(self, title, code=None):
        self.title = title
        self.code = code

    def __str__(self):
        return self.title


class GroupCollection:
    def __init__(self, groups):
        self.groups = groups

    def all(self):
        return self.groups


class HistoryHeaderTest(SimpleTestCase):
    def setUp(self):
        self.region = NamedEntity("Камчатский край", "41")
        self.city = NamedEntity("Новосибирск")
        self.group = SimpleNamespace(name="museums", title="Музеи")

    def tourism_record(self, **kwargs):
        record = SimpleNamespace(tourism_type="gastro", sight_group=None, **kwargs)
        record.get_tourism_type_display = lambda: "Гастрономический туризм"
        return record

    def test_region_interest_from_city_renders_editable_template(self):
        record = self.tourism_record(home_code=self.region, code=self.city)

        html = _render_history_header(record, "popularity", "region_city")

        self.assertIn("интерес к&nbsp;региону", html)
        self.assertIn("из&nbsp;города", html)
        self.assertIn("вид туризма", html)
        self.assertIn("Камчатский край", html)
        self.assertIn("Новосибирск", html)
        self.assertIn("/static/img/blazon/41.svg", html)
        self.assertIn("#city", html)
        self.assertIn("#gastro", html)
        self.assertIn("Гастрономический туризм", html)

    def test_city_interest_from_region_uses_inverse_entity_icons(self):
        record = self.tourism_record(home_code=self.city, code=self.region)

        html = _render_history_header(record, "popularity", "city_region")

        self.assertIn("из&nbsp;региона", html)
        self.assertIn("#city", html)
        self.assertIn("/static/img/blazon/41.svg", html)

    def test_sight_interest_uses_sight_group_for_entity_icon(self):
        sight = NamedEntity("Краеведческий музей")
        sight.group = GroupCollection([self.group])
        record = SimpleNamespace(
            sight=sight,
            home_code=self.region,
            code=self.city,
        )

        html = _render_history_header(record, "popularity", "sight_city")

        self.assertIn("Краеведческий музей", html)
        self.assertIn("интерес к&nbsp;точке притяжения", html)
        self.assertIn("#museums", html)
        self.assertNotIn("тип точки притяжения", html)

    def test_rating_headers_use_current_block_layout(self):
        cases = (
            ("region", self.region, "image"),
            ("city", self.city, "sprite"),
        )
        for entity_type, entity, icon_kind in cases:
            with self.subTest(entity_type=entity_type):
                record = self.tourism_record(home_code=entity)
                html = _render_history_header(record, "rating_place", entity_type)
                self.assertIn("позиция в рейтинге", html)
                self.assertIn("вид туризма", html)
                self.assertIn("#gastro", html)
                if icon_kind == "image":
                    self.assertIn("/static/img/blazon/41.svg", html)
                else:
                    self.assertIn("#city", html)

        sight = NamedEntity("Краеведческий музей")
        sight.group = GroupCollection([self.group])
        record = SimpleNamespace(sight=sight, sight_group=None)
        html = _render_history_header(record, "rating_place", "sight")
        self.assertIn("позиция в рейтинге", html)
        self.assertIn("Краеведческий музей", html)
        self.assertIn("#museums", html)
        self.assertNotIn("вид туризма", html)

    def test_all_tourism_adds_explicit_classification_block(self):
        record = SimpleNamespace(
            home_code=self.region,
            tourism_type=None,
            sight_group=None,
        )

        html = _render_history_header(record, "rating_place", "region")

        self.assertIn("вид туризма", html)
        self.assertIn("все виды туризма", html)
        self.assertIn("#tourism", html)

    def test_sight_uses_first_group_in_model_order(self):
        first = SimpleNamespace(name="artgallery", title="Галереи")
        second = SimpleNamespace(name="theatre", title="Театры")
        sight = NamedEntity("Большой театр")
        sight.group = GroupCollection([first, second])
        record = SimpleNamespace(sight=sight, sight_group=None)

        html = _render_history_header(record, "rating_place", "sight")

        self.assertIn("#artgallery", html)
        self.assertNotIn("#theatre", html)

    def test_sight_without_groups_keeps_location_fallback(self):
        sight = NamedEntity("Точка без группы")
        sight.group = GroupCollection([])
        record = SimpleNamespace(sight=sight, sight_group=None)

        html = _render_history_header(record, "rating_place", "sight")

        self.assertIn("#location", html)
        self.assertNotIn("тип точки притяжения", html)

    def test_dynamic_values_are_escaped_by_django(self):
        unsafe_region = NamedEntity("<script>alert('x')</script>", "41")
        record = self.tourism_record(home_code=unsafe_region, code=self.city)

        html = _render_history_header(record, "popularity", "region_city")

        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
