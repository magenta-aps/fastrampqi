# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
# pylint: disable=protected-access
"""Test the FastAPIIntegrationSystem."""
from typing import Any

from fastramqpi.config import FastAPIIntegrationSystemSettings
from fastramqpi.config import Settings
from fastramqpi.fastapi import build_information
from fastramqpi.fastapi import FastAPIIntegrationSystem
from fastramqpi.fastapi import update_build_information


def test_settings_set() -> None:
    """Ensure that without override, we still get a settings object."""
    system = FastAPIIntegrationSystem("test")
    assert system.settings is not None
    assert isinstance(system.settings, FastAPIIntegrationSystemSettings)


def test_settings_override() -> None:
    """Ensure that with override, our setting is bound as-is."""
    settings = Settings()
    system = FastAPIIntegrationSystem("test", settings)
    assert system.settings is not None
    assert isinstance(system.settings, Settings)
    assert system.settings == settings


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
