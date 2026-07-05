from types import SimpleNamespace
from unittest import mock

import pytest

from acesta.stats.helpers.audience import get_audience_quantity
from acesta.stats.helpers.audience import prepare_audience_groups


def audience_record(quantity, coefficient=1):
    return SimpleNamespace(v_type_sex_age=quantity, coeff=coefficient)


def test_prepare_audience_groups_removes_non_positive_displayed_quantities():
    groups, percentile = prepare_audience_groups(
        [audience_record(10), audience_record(0), audience_record(10, -1)]
    )

    assert [get_audience_quantity(group) for group in groups] == [10]
    assert percentile == 10


def test_priority_percentile_uses_displayed_quantity_and_preserves_order():
    groups, percentile = prepare_audience_groups(
        [
            audience_record(100),
            audience_record(60, 2),
            audience_record(110),
            audience_record(0),
        ]
    )

    quantities = [get_audience_quantity(group) for group in groups]
    priority_quantities = [quantity for quantity in quantities if quantity > percentile]

    assert quantities == [100, 120, 110]
    assert percentile == pytest.approx(119)
    assert priority_quantities == [120]


def test_quantity_equal_to_percentile_is_not_priority():
    groups, percentile = prepare_audience_groups(
        [audience_record(25), audience_record(25)]
    )

    assert all(get_audience_quantity(group) <= percentile for group in groups)


def test_empty_audience_key_does_not_preload_an_arbitrary_region():
    from acesta.stats.dash.audience import update_audience

    title, title_class, payload = update_audience(
        "", user=SimpleNamespace(is_extended=True)
    )

    assert title == ""
    assert title_class == "d-none"
    assert payload["empty"].startswith("Выберите заинтересованный регион")


def test_audience_callback_returns_compact_group_payload():
    from acesta.stats.dash import audience as audience_module

    record = SimpleNamespace(
        v_type_sex_age=100,
        coeff=1,
        sex="m",
        age="25-34",
        tourism_type="active",
        v_type_in_pair=25,
        v_sex_age=100,
        v_sex_age_child_6=10,
        v_sex_age_child_7_12=20,
        v_sex_age_parents=30,
    )
    with mock.patch.object(audience_module, "get_object_title", return_value="Регион"):
        with mock.patch.object(audience_module, "get_audience", return_value=[record]):
            with mock.patch.object(
                audience_module,
                "get_indicator_data",
                return_value=None,
            ):
                title, title_class, payload = audience_module.update_audience(
                    "01__regions", user=SimpleNamespace(is_extended=True)
                )

    assert title.endswith(" в регионе Регион")
    assert title_class == "bg-white d-block"
    assert payload["groups"][0]["q"] == "1\xa0000"
    assert "children" not in payload["groups"][0]
