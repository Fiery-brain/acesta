from types import SimpleNamespace

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
