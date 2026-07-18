from django import test
from django.test import override_settings

from acesta.base.models import ProcessCycle
from acesta.base.models import ProcessRegistry
from acesta.base.models import ProcessStageNotReady


PROCESS_CYCLES = {
    "popularity": {
        "stages": {
            "kernels": {},
            "popularity_sights": {
                "requires": ("kernels",),
            },
            "fill": {
                "requires": ("popularity_sights",),
            },
        },
    },
}


@override_settings(PROCESS_CYCLES=PROCESS_CYCLES)
class ProcessCycleTest(test.TestCase):
    def test_complete_stage_stores_unique_completed_stage(self):
        cycle = ProcessCycle("popularity", "01")

        cycle.complete_stage("kernels")
        cycle.complete_stage("kernels")

        marker = ProcessRegistry.get_open("popularity", "region_cycle", "01")
        self.assertEqual(marker.get_data("completed_stages"), ["kernels"])
        self.assertIsNone(marker.get_data("current_stage"))

    def test_start_stage_checks_required_stages(self):
        cycle = ProcessCycle("popularity", "01")

        with self.assertRaises(ProcessStageNotReady) as context:
            cycle.start_stage("popularity_sights")

        self.assertEqual(context.exception.missing_stages, ("kernels",))

    def test_force_stage_writes_forced_stage(self):
        cycle = ProcessCycle("popularity", "01")

        cycle.start_stage("popularity_sights", force=True)

        marker = ProcessRegistry.get_open("popularity", "region_cycle", "01")
        self.assertEqual(marker.get_data("current_stage"), "popularity_sights")
        self.assertEqual(marker.get_data("forced_stages"), ["popularity_sights"])

    def test_is_ready_for_uses_config_requirements(self):
        cycle = ProcessCycle("popularity", "01")

        self.assertFalse(cycle.is_ready_for("popularity_sights"))

        cycle.complete_stage("kernels")

        self.assertTrue(cycle.is_ready_for("popularity_sights"))

    def test_update_changes_modified_datetime(self):
        cycle = ProcessCycle("popularity", "01")
        marker = cycle.marker
        old_modified = marker.modified

        cycle.start_stage("kernels")
        marker.refresh_from_db()

        self.assertGreater(marker.modified, old_modified)
