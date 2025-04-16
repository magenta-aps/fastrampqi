# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import os
from typing import Iterator
from uuid import uuid4

import pytest

SETTINGS_KEY_1 = str(uuid4())
SETTINGS_KEY_2 = str(uuid4())
SETTINGS_VALUE = "GLOBAL_VALUE"
os.environ[SETTINGS_KEY_1] = SETTINGS_VALUE
os.environ[SETTINGS_KEY_2] = SETTINGS_VALUE


@pytest.fixture
def set_environment_key(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv(SETTINGS_KEY_2, "fixture_value")
    yield


def test_unittest_empty_environment() -> None:
    assert os.environ.get(SETTINGS_KEY_1) is None
    assert os.environ.get(SETTINGS_KEY_2) is None


@pytest.mark.usefixtures("set_environment_key")
def test_unittest_empty_environment_with_overrides() -> None:
    assert os.environ.get(SETTINGS_KEY_1) is None
    assert os.environ.get(SETTINGS_KEY_2) == "fixture_value"


@pytest.mark.integration_test
def test_integration_test_normal_environment() -> None:
    assert os.environ.get(SETTINGS_KEY_1) == SETTINGS_VALUE
    assert os.environ.get(SETTINGS_KEY_2) == SETTINGS_VALUE


@pytest.mark.integration_test
@pytest.mark.usefixtures("set_environment_key")
def test_integration_test_normal_environment_with_overrides() -> None:
    assert os.environ.get(SETTINGS_KEY_1) == SETTINGS_VALUE
    assert os.environ.get(SETTINGS_KEY_2) == "fixture_value"
