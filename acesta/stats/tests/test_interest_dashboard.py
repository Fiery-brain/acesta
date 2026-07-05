import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import geopandas as gpd
from django.conf import settings
from django.test import TestCase
from shapely.geometry import Polygon

from acesta.geo.models import Region


class PopularityTableTrendTest(TestCase):
    class PopularityRows:
        def __init__(self, model, rows):
            self.model = model
            self.rows = rows

        def values(self, *columns):
            return [
                {column: row.get(column) for column in columns} for row in self.rows
            ]

    def build_table(self, model, rows, sort_by=None):
        from acesta.stats.dash.helpers.interest import get_ppt_df

        return get_ppt_df(self.PopularityRows(model, rows), sort_by or []).to_dict(
            "records"
        )

    def test_region_rows_show_growth_decline_and_neutral_slots(self):
        from acesta.stats.models import RegionRegionPopularity

        rows = [
            {
                "code__title": "Рост",
                "code": "01",
                "qty": 120,
                "ppt": 150,
                "modified": date(2026, 6, 28),
                "history": [
                    {"date": "2026-06-20", "qty": 999, "mean": 999},
                    {"date": "2026-05-10", "qty": 80, "mean": 110},
                    {"date": "2026-05-25", "qty": 100, "mean": 120},
                ],
            },
            {
                "code__title": "Снижение",
                "code": "02",
                "qty": 80,
                "ppt": 90,
                "modified": date(2026, 6, 28),
                "history": [{"date": "2026-05-25", "qty": 100, "mean": 120}],
            },
            {
                "code__title": "Без изменений",
                "code": "03",
                "qty": 100,
                "ppt": 120,
                "modified": date(2026, 6, 28),
                "history": [{"date": "2026-05-25", "qty": 100, "mean": 120}],
            },
            {
                "code__title": "Без истории",
                "code": "04",
                "qty": 100,
                "ppt": 120,
                "modified": date(2026, 6, 28),
                "history": [],
            },
        ]

        growth, decline, equal, missing = self.build_table(RegionRegionPopularity, rows)

        self.assertIn("120", growth["qty_display"])
        self.assertIn("150%", growth["ppt_display"])
        self.assertIn("place_change", growth["qty_display"])
        self.assertIn("&uarr;", growth["ppt_display"])
        self.assertIn("place_change_negative", decline["qty_display"])
        self.assertIn("&darr;", decline["ppt_display"])
        self.assertIn(">-</span>", equal["qty_display"])
        self.assertIn("place_change_neural", equal["ppt_display"])
        self.assertIn(">-</span>", missing["qty_display"])
        self.assertIn("place_change_neural", missing["ppt_display"])
        self.assertEqual(growth["ppt"], 1.5)

    def test_city_rows_use_previous_month_across_year_boundary(self):
        from acesta.stats.models import RegionCityPopularity

        rows = [
            {
                "code__title": "Город",
                "code": 1,
                "qty": 150,
                "ppt": 130,
                "modified": date(2026, 1, 15),
                "history": [
                    {"date": "2026-01-10", "qty": 999, "mean": 999},
                    {"date": "2025-12-20", "qty": 100, "mean": 120},
                ],
            }
        ]

        row = self.build_table(RegionCityPopularity, rows)[0]

        self.assertIn("&uarr;", row["qty_display"])
        self.assertIn("&uarr;", row["ppt_display"])

    def test_display_columns_keep_numeric_sorting(self):
        from acesta.stats.models import RegionRegionPopularity

        rows = [
            {
                "code__title": "Девять",
                "code": "01",
                "qty": 9,
                "ppt": 9,
                "modified": date(2026, 6, 28),
                "history": [],
            },
            {
                "code__title": "Сто",
                "code": "02",
                "qty": 100,
                "ppt": 100,
                "modified": date(2026, 6, 28),
                "history": [],
            },
        ]

        ascending = self.build_table(
            RegionRegionPopularity,
            rows,
            [{"column_id": "qty_display", "direction": "asc"}],
        )
        descending = self.build_table(
            RegionRegionPopularity,
            rows,
            [{"column_id": "qty_display", "direction": "desc"}],
        )

        self.assertEqual([row["qty"] for row in ascending], [9, 100])
        self.assertEqual([row["qty"] for row in descending], [100, 9])

    def test_name_column_sorts_alphabetically_in_both_directions(self):
        from acesta.stats.models import RegionRegionPopularity

        rows = [
            {
                "code__title": "Ярославская область",
                "code": "76",
                "qty": 100,
                "ppt": 100,
                "modified": date(2026, 6, 28),
                "history": [],
            },
            {
                "code__title": "Алтайский край",
                "code": "22",
                "qty": 100,
                "ppt": 100,
                "modified": date(2026, 6, 28),
                "history": [],
            },
            {
                "code__title": "Алтайский край",
                "code": "04",
                "qty": 100,
                "ppt": 100,
                "modified": date(2026, 6, 28),
                "history": [],
            },
        ]

        ascending = self.build_table(
            RegionRegionPopularity,
            rows,
            [{"column_id": "code__title", "direction": "asc"}],
        )
        descending = self.build_table(
            RegionRegionPopularity,
            rows,
            [{"column_id": "code__title", "direction": "desc"}],
        )

        self.assertEqual(
            [(row["code__title"], row["code"]) for row in ascending],
            [
                ("Алтайский край", "04"),
                ("Алтайский край", "22"),
                ("Ярославская область", "76"),
            ],
        )
        self.assertEqual(
            [row["code__title"] for row in descending],
            ["Ярославская область", "Алтайский край", "Алтайский край"],
        )


class InterestTableColumnsTest(unittest.TestCase):
    def test_column_heading_matches_selected_source_area(self):
        from acesta.stats.dash.interest.ui import update_interest_table_columns

        region_columns = update_interest_table_columns(settings.AREA_REGIONS)
        city_columns = update_interest_table_columns(settings.AREA_CITIES)
        fallback_columns = update_interest_table_columns(None)

        self.assertEqual(region_columns[1]["name"], "Регион")
        self.assertEqual(city_columns[1]["name"], "Город")
        self.assertEqual(fallback_columns[1]["name"], "Регион")


class SelectedInterestRowTest(TestCase):
    def test_session_save_waits_until_restoration_is_complete(self):
        from dash.exceptions import PreventUpdate

        from acesta.stats.dash.interest.interest import save_interest_session_state

        with self.assertRaises(PreventUpdate):
            save_interest_session_state(
                "",
                settings.AREA_REGIONS,
                settings.AREA_REGIONS,
                [{"column_id": "qty", "direction": "asc"}],
                None,
                "regions_0",
                False,
                {},
            )

    def test_hydration_opens_only_after_controls_and_table_match(self):
        from dash.exceptions import PreventUpdate

        from acesta.stats.dash.interest import interest as interest_module

        state = {
            "homeArea": settings.AREA_CITIES,
            "interesantArea": settings.AREA_CITIES,
            "tourismType": "museum",
            "sortBy": [{"column_id": "ppt_display", "direction": "desc"}],
            "targetKey": "cities_22",
        }
        table_state = {key: value for key, value in state.items() if key != "targetKey"}
        user = SimpleNamespace(current_region=SimpleNamespace(code="40"))

        with mock.patch.object(
            interest_module,
            "get_validated_target_key",
            return_value="cities_22",
        ):
            with self.assertRaises(PreventUpdate):
                interest_module.mark_interest_session_hydrated(
                    "museum",
                    settings.AREA_REGIONS,
                    settings.AREA_CITIES,
                    state["sortBy"],
                    "regions_0",
                    table_state,
                    state,
                    user=user,
                )
            self.assertTrue(
                interest_module.mark_interest_session_hydrated(
                    "museum",
                    settings.AREA_CITIES,
                    settings.AREA_CITIES,
                    state["sortBy"],
                    "cities_22",
                    table_state,
                    state,
                    user=user,
                )
            )

    def test_title_uses_restored_target_key(self):
        from acesta.stats.dash.interest import ui as ui_module

        city = SimpleNamespace(title="Калуга")
        city_queryset = mock.Mock()
        city_queryset.first.return_value = city
        sight = SimpleNamespace(title="Музей космонавтики")
        sight_queryset = mock.Mock()
        sight_queryset.first.return_value = sight
        user = SimpleNamespace(
            is_extended=True,
            current_region=SimpleNamespace(code="40"),
        )

        with mock.patch.object(
            ui_module.City.objects, "filter", return_value=city_queryset
        ):
            city_title = ui_module.update_title(
                settings.AREA_CITIES,
                "cities_22",
                "",
                user=user,
            )
        with mock.patch.object(
            ui_module.Sight.objects, "filter", return_value=sight_queryset
        ):
            sight_title = ui_module.update_title(
                settings.AREA_SIGHTS,
                "sights_88",
                "museum",
                user=user,
            )

        self.assertEqual(city_title, "Интерес к городу Калуга")
        self.assertEqual(sight_title, "Интерес к объекту Музей космонавтики")

    def test_session_state_is_rejected_after_access_expires(self):
        from acesta.stats.dash.helpers.interest import get_restorable_interest_state

        user = SimpleNamespace(
            is_extended=False,
            current_region=SimpleNamespace(code="40", region_type="region"),
        )
        restored = get_restorable_interest_state(
            {
                "version": 1,
                "regionCode": "40",
                "homeArea": settings.AREA_SIGHTS,
                "interesantArea": settings.AREA_CITIES,
                "tourismType": "museum",
                "sortBy": [{"column_id": "ppt_display", "direction": "desc"}],
                "sourceRowId": "77",
                "targetKey": "sights_88",
            },
            user,
        )

        self.assertEqual(restored["homeArea"], settings.AREA_REGIONS)
        self.assertEqual(restored["interesantArea"], settings.AREA_REGIONS)
        self.assertEqual(restored["tourismType"], "")
        self.assertIsNone(restored["sourceRowId"])
        self.assertEqual(restored["targetKey"], "regions_0")

    def test_session_state_from_another_region_is_rejected(self):
        from acesta.stats.dash.helpers.interest import get_restorable_interest_state

        user = SimpleNamespace(
            is_extended=True,
            current_region=SimpleNamespace(code="40", region_type="region"),
        )
        restored = get_restorable_interest_state(
            {
                "version": 1,
                "regionCode": "79",
                "homeArea": settings.AREA_SIGHTS,
                "interesantArea": settings.AREA_CITIES,
                "sourceRowId": "77",
            },
            user,
        )

        self.assertEqual(restored["homeArea"], settings.AREA_REGIONS)
        self.assertIsNone(restored["sourceRowId"])

    def test_rank_zero_extended_state_uses_existing_access_logic(self):
        from acesta.stats.dash.helpers.interest import get_restorable_interest_state

        user = SimpleNamespace(
            is_extended=True,
            is_set_tourism_types=False,
            current_region=SimpleNamespace(
                code="40",
                rank=0,
                region_type="region",
            ),
        )
        state = {
            "version": 1,
            "regionCode": "40",
            "homeArea": settings.AREA_SIGHTS,
            "interesantArea": settings.AREA_CITIES,
            "tourismType": "museum",
            "sortBy": [{"column_id": "ppt_display", "direction": "desc"}],
            "sourceRowId": "77",
            "targetKey": "sights_88",
        }

        self.assertEqual(
            get_restorable_interest_state(state, user),
            {
                **state,
                "version": 2,
                "sortBy": [{"column_id": "ppt_display", "direction": "asc"}],
            },
        )

    def test_legacy_name_sort_keeps_its_direction(self):
        from acesta.stats.dash.helpers.interest import get_restorable_interest_state

        user = SimpleNamespace(
            is_extended=True,
            is_set_tourism_types=False,
            current_region=SimpleNamespace(code="40", region_type="region"),
        )
        restored = get_restorable_interest_state(
            {
                "version": 1,
                "regionCode": "40",
                "homeArea": settings.AREA_REGIONS,
                "interesantArea": settings.AREA_REGIONS,
                "tourismType": "",
                "sortBy": [{"column_id": "code__title", "direction": "desc"}],
                "sourceRowId": None,
                "targetKey": "regions_0",
            },
            user,
        )

        self.assertEqual(restored["version"], 2)
        self.assertEqual(
            restored["sortBy"],
            [{"column_id": "code__title", "direction": "desc"}],
        )

    def test_legacy_numeric_sort_keeps_order_with_corrected_direction(self):
        from acesta.stats.dash.helpers.interest import get_restorable_interest_state

        user = SimpleNamespace(
            is_extended=True,
            is_set_tourism_types=False,
            current_region=SimpleNamespace(code="40", region_type="region"),
        )
        restored = get_restorable_interest_state(
            {
                "version": 1,
                "regionCode": "40",
                "homeArea": settings.AREA_REGIONS,
                "interesantArea": settings.AREA_REGIONS,
                "tourismType": "",
                "sortBy": [{"column_id": "qty", "direction": "asc"}],
                "sourceRowId": None,
                "targetKey": "regions_0",
            },
            user,
        )

        self.assertEqual(restored["version"], 2)
        self.assertEqual(
            restored["sortBy"],
            [{"column_id": "qty_display", "direction": "desc"}],
        )

    def test_saved_source_row_is_restored_only_when_it_still_exists(self):
        import pandas as pd

        from acesta.stats.dash.interest import interest as interest_module

        user = SimpleNamespace(
            is_extended=True,
            is_set_tourism_types=False,
            current_region=SimpleNamespace(code="40", region_type="region"),
        )
        state = {
            "version": 2,
            "regionCode": "40",
            "homeArea": settings.AREA_REGIONS,
            "interesantArea": settings.AREA_REGIONS,
            "tourismType": "",
            "sortBy": [{"column_id": "qty_display", "direction": "desc"}],
            "sourceRowId": "37",
            "targetKey": "regions_0",
        }
        table = pd.DataFrame(
            [{"id": "37", "code": "37", "code__title": "Ивановская область"}]
        )

        with mock.patch.object(interest_module, "get_interest"):
            with mock.patch.object(interest_module, "get_ppt_df", return_value=table):
                _, selected_cells, active_cell, _ = interest_module.update_interest(
                    "",
                    settings.AREA_REGIONS,
                    settings.AREA_REGIONS,
                    None,
                    "regions_0",
                    [{"column_id": "qty_display", "direction": "desc"}],
                    None,
                    state,
                    user=user,
                    callback_context=SimpleNamespace(triggered=[]),
                )

        self.assertEqual(active_cell["row_id"], "37")
        self.assertEqual(len(selected_cells), 3)

    def test_tourism_type_survives_navigation_for_extended_user(self):
        from acesta.stats.dash.interest.ui import update_tourism_type

        user = SimpleNamespace(
            is_extended=True,
            is_set_tourism_types=True,
            get_current_tourism_type=lambda value=None: (
                value if value in {"museum", "spa"} else "museum"
            ),
        )
        request = SimpleNamespace(user=user)

        for home_area in (
            settings.AREA_REGIONS,
            settings.AREA_CITIES,
            settings.AREA_SIGHTS,
        ):
            with self.subTest(home_area=home_area):
                self.assertEqual(
                    update_tourism_type(home_area, None, "spa", True, request=request),
                    "spa",
                )

    def test_unavailable_tourism_type_uses_existing_access_fallback(self):
        from acesta.stats.dash.interest.ui import update_tourism_type

        user = SimpleNamespace(
            is_extended=True,
            is_set_tourism_types=True,
            get_current_tourism_type=lambda value=None: "museum",
        )

        self.assertEqual(
            update_tourism_type(
                settings.AREA_CITIES,
                None,
                "beach",
                True,
                request=SimpleNamespace(user=user),
            ),
            "museum",
        )

    def test_tourism_type_keeps_existing_initial_and_free_defaults(self):
        from acesta.stats.dash.interest.ui import update_tourism_type

        extended_user = SimpleNamespace(
            is_extended=True,
            is_set_tourism_types=False,
        )
        basic_user = SimpleNamespace(is_extended=False)

        self.assertEqual(
            update_tourism_type(
                settings.AREA_REGIONS,
                None,
                None,
                False,
                request=SimpleNamespace(user=extended_user),
            ),
            "",
        )
        self.assertEqual(
            update_tourism_type(
                settings.AREA_REGIONS,
                None,
                "museum",
                False,
                request=SimpleNamespace(user=basic_user),
            ),
            "",
        )

    def test_callback_triggered_id_uses_django_plotly_dash_context(self):
        from acesta.stats.dash.helpers.interest import get_callback_triggered_id

        callback_context = SimpleNamespace(
            triggered=[{"prop_id": "table-interesants.active_cell"}]
        )

        self.assertEqual(
            get_callback_triggered_id(callback_context), "table-interesants"
        )

    def test_callback_triggered_id_is_none_without_trigger(self):
        from acesta.stats.dash.helpers.interest import get_callback_triggered_id

        self.assertIsNone(get_callback_triggered_id(None))
        self.assertIsNone(get_callback_triggered_id(SimpleNamespace(triggered=[])))

    def test_callback_triggered_id_reads_map_click(self):
        from acesta.stats.dash.helpers.interest import get_callback_triggered_id

        callback_context = SimpleNamespace(triggered=[{"prop_id": "map.clickData"}])

        self.assertEqual(get_callback_triggered_id(callback_context), "map")

    def test_selection_uses_stable_row_id(self):
        from acesta.stats.dash.interest.map import get_selected_interest_row

        table_data = [
            {
                "id": "37",
                "code": "37",
                "code__title": "Ивановская область",
                "qty": 1780,
                "ppt": 0.35,
            },
            {
                "id": "40",
                "code": "40",
                "code__title": "Калужская область",
                "qty": 476209,
                "ppt": 57.56,
            },
        ]

        selected = get_selected_interest_row(
            {"row": 1, "row_id": "37"},
            table_data,
        )

        self.assertEqual(selected["code"], "37")
        self.assertEqual(selected["qty"], 1780)


class RegionMapCallbackTest(TestCase):
    def setUp(self):
        self.regions = gpd.GeoDataFrame(
            {
                "name": ["Калужская область", "Ивановская область"],
                "qty": [476209, 1780],
                "ppt": [5756, 35],
            },
            geometry=[
                Polygon([(35, 53), (37, 53), (37, 55), (35, 55)]),
                Polygon([(40, 56), (42, 56), (42, 58), (40, 58)]),
            ],
            index=["40", "37"],
            crs="EPSG:4326",
        )

    def test_table_click_updates_connection_overlay_card_and_balloon(self):
        from acesta.stats.dash.interest import map as map_module

        region = SimpleNamespace(
            code="40",
            title="Калужская область",
            federal_district="ЦФО",
            rank=2,
            description="Описание",
            center_lat=54,
            center_lon=36,
            zoom_regions=3.5,
            zoom_cities=5,
            get_federal_district_display=lambda: "Центральный",
            get_rank_display=lambda: "Средний",
        )
        user = SimpleNamespace(current_region=region, is_extended=True)
        request = SimpleNamespace(COOKIES={"innerHeight": "768"}, user=user)
        table_data = [
            {
                "id": "37",
                "code": "37",
                "code__title": "Ивановская область",
                "qty": 1780,
                "ppt": 0.35,
            }
        ]

        with mock.patch.object(
            map_module, "get_map_df", return_value=self.regions.copy()
        ):
            figure, card, balloons = map_module.update_map(
                "",
                settings.AREA_REGIONS,
                settings.AREA_REGIONS,
                {"row": 0, "row_id": "37"},
                "regions_0",
                {"width": 700, "height": 500},
                table_data,
                user=user,
                request=request,
            )

        self.assertEqual([trace.type for trace in figure.data], ["choroplethmap"] * 2)
        self.assertGreaterEqual(len(figure.layout.map.layers), 3)
        self.assertEqual(card[0].children[1].children[1].children, region.title)
        self.assertEqual(len(balloons), 1)
        balloon_props = balloons[0].to_plotly_json()["props"]
        self.assertEqual(balloon_props["data-role"], "source")
        self.assertEqual(
            balloon_props["children"][1].children,
            "Ивановская область",
        )
        self.assertNotIn(
            "но аудитория ограничена",
            [child.children for child in balloon_props["children"]],
        )
        camera = figure.layout.meta["acestaInterestCamera"]
        self.assertIn("regions_37", camera["key"])
        self.assertIn("regions_40", camera["key"])
        self.assertEqual(camera["center"], figure.layout.map.center.to_plotly_json())
        self.assertEqual(camera["zoom"], figure.layout.map.zoom)

    def test_sight_target_without_source_preserves_client_camera(self):
        from acesta.stats.dash.interest import map as map_module

        region = SimpleNamespace(
            code="40",
            title="Калужская область",
            federal_district="ЦФО",
            rank=2,
            description="Описание",
            center_lat=54,
            center_lon=36,
            zoom_regions=3.5,
            zoom_cities=5,
            get_federal_district_display=lambda: "Центральный",
            get_rank_display=lambda: "Средний",
        )
        sight = SimpleNamespace(
            pk=301,
            id=301,
            title="Точка притяжения",
            lon=36.5,
            lat=54.5,
            qty=100,
            address="",
            group=SimpleNamespace(all=lambda: []),
        )
        user = SimpleNamespace(current_region=region, is_extended=True)
        request = SimpleNamespace(COOKIES={"innerHeight": "768"}, user=user)
        client_camera = {
            "center": {"lon": 37.125, "lat": 55.25},
            "zoom": 9.75,
        }

        with mock.patch.object(
            map_module, "get_map_df", return_value=self.regions.copy()
        ):
            with mock.patch.object(
                map_module,
                "resolve_target_key",
                return_value="sights_301",
            ), mock.patch.object(map_module, "get_sights", return_value=[sight]):
                figure, _, _ = map_module.update_map(
                    "",
                    settings.AREA_SIGHTS,
                    settings.AREA_REGIONS,
                    None,
                    "sights_301",
                    {"width": 700, "height": 500},
                    [],
                    client_camera,
                    user=user,
                    request=request,
                )

        self.assertEqual(
            figure.layout.map.center.to_plotly_json(), client_camera["center"]
        )
        self.assertEqual(figure.layout.map.zoom, client_camera["zoom"])
        self.assertEqual(
            figure.layout.meta["acestaInterestCamera"]["center"],
            client_camera["center"],
        )
        self.assertEqual(
            figure.layout.meta["acestaInterestCamera"]["zoom"],
            client_camera["zoom"],
        )

    def test_sight_connection_keeps_automatic_camera(self):
        from acesta.stats.dash.interest import map as map_module

        region = SimpleNamespace(
            code="40",
            title="Калужская область",
            federal_district="ЦФО",
            rank=2,
            description="Описание",
            center_lat=54,
            center_lon=36,
            zoom_regions=3.5,
            zoom_cities=5,
            get_federal_district_display=lambda: "Центральный",
            get_rank_display=lambda: "Средний",
        )
        sight = SimpleNamespace(
            pk=301,
            id=301,
            title="Точка притяжения",
            lon=36.5,
            lat=54.5,
            qty=100,
            address="",
            group=SimpleNamespace(all=lambda: []),
        )
        user = SimpleNamespace(current_region=region, is_extended=True)
        request = SimpleNamespace(COOKIES={"innerHeight": "768"}, user=user)
        table_data = [
            {
                "id": "37",
                "code": "37",
                "code__title": "Ивановская область",
                "qty": 1780,
                "ppt": 135,
            }
        ]

        with mock.patch.object(
            map_module, "get_map_df", return_value=self.regions.copy()
        ):
            with mock.patch.object(map_module, "get_sights", return_value=[sight]):
                figure, _, _ = map_module.update_map(
                    "",
                    settings.AREA_SIGHTS,
                    settings.AREA_REGIONS,
                    {"row": 0, "row_id": "37"},
                    "sights_301",
                    {"width": 700, "height": 500},
                    table_data,
                    {"center": {"lon": 37.125, "lat": 55.25}, "zoom": 18},
                    user=user,
                    request=request,
                )

        self.assertNotEqual(figure.layout.map.zoom, 18)


class InterestMapCameraUnitTest(unittest.TestCase):
    def test_camera_validation_accepts_only_finite_map_values(self):
        from acesta.stats.dash.interest.map import get_interest_map_camera

        self.assertEqual(
            get_interest_map_camera(
                {"center": {"lon": 43.25, "lat": 43.5}, "zoom": 9.75}
            ),
            ({"lon": 43.25, "lat": 43.5}, 9.75),
        )
        self.assertIsNone(
            get_interest_map_camera(
                {"center": {"lon": 43.25, "lat": 43.5}, "zoom": "nan"}
            )
        )
        self.assertIsNone(
            get_interest_map_camera({"center": {"lon": 43.25, "lat": 95}, "zoom": 9.75})
        )

    def test_client_applies_camera_only_after_a_new_plot(self):
        script = (
            Path(__file__).resolve().parents[2] / "static/js/dashboard.interest.js"
        ).read_text()

        camera_sync = script.split("function getInterestMapCameraIntent", 1)[1].split(
            "function updateInterestMapArrows", 1
        )[0]
        self.assertIn('graph.on("plotly_afterplot"', camera_sync)
        self.assertIn("map.jumpTo", camera_sync)
        self.assertIn("cameraDiffers", camera_sync)
        self.assertIn("lastAppliedInterestMapCameraIntent", camera_sync)
        self.assertIn(
            "intentSignature === lastAppliedInterestMapCameraIntent",
            camera_sync,
        )
        self.assertIn(
            "getInterestMapCameraIntentSignature(intent) ===",
            camera_sync,
        )
        self.assertNotIn('map.on("move"', camera_sync)

    def test_client_saves_camera_after_map_movement(self):
        script = (
            Path(__file__).resolve().parents[2] / "static/js/dashboard.interest.js"
        ).read_text()

        self.assertIn('set_props("interest-map-camera"', script)
        self.assertIn('on("moveend", updateInterestMapCameraState)', script)
        self.assertIn('off("moveend", updateInterestMapCameraState)', script)


class RegionMapCardTest(TestCase):
    def test_detailed_card_omits_empty_description_and_includes_blazon(self):
        from acesta.stats.dash.interest.map import get_home_region_card

        region = Region(
            code="40",
            title="Тестовый регион",
            federal_district="ЦФО",
            rank=2,
            description="",
        )

        card = get_home_region_card(region)

        self.assertEqual(len(card), 2)
        self.assertEqual(len(card[0].children), 2)
        self.assertEqual(card[0].children[0].src, "/static/img/blazon/40.svg")
        self.assertEqual(
            card[0].children[1].children[0].children,
            "Анализируем регион",
        )
        self.assertEqual(card[1].children[1].children, "Средний потенциал")
