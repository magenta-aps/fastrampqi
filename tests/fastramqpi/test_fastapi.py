# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# pylint: disable=protected-access
"""Test the FastAPIIntegrationSystem."""

from typing import Any

from fastramqpi.app import build_information
from fastramqpi.app import update_build_information


def clear_metric_value(metric: Any) -> None:
    """Get the value of a given metric with the given label-set.

    Args:
        metric: The metric to query.

    Returns:
        The metric value.
    """
    metric.clear()


def test_build_information() -> None:
    """Test that build metrics are updated as expected."""
    clear_metric_value(build_information)
    assert build_information._value == {}
    update_build_information("1.0.0", "cafebabe")
    assert build_information._value == {
        "version": "1.0.0",
        "hash": "cafebabe",
    }
