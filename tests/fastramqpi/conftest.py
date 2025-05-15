# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# pylint: disable=redefined-outer-name
"""This module contains pytest specific code, fixtures and helpers."""

from typing import Generator

import pytest
from pytest import MonkeyPatch

from fastramqpi.config import Settings
from fastramqpi.ramqp.config import AMQPConnectionSettings


@pytest.fixture(scope="session")
def monkeysession() -> Generator[MonkeyPatch, None, None]:
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture
def settings() -> Settings:
    """Settings object with the required variables set to dummy values.."""
    return Settings(
        client_id="orggatekeeper",
        client_secret="hunter2",
        amqp=AMQPConnectionSettings(
            url="amqp://guest:guest@msg-broker:5672/os2mo",
        ),
    )
