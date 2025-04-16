# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
# pylint: disable=redefined-outer-name
"""This module contains pytest specific code, fixtures and helpers."""

from typing import Any
from typing import Callable
from typing import Generator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from fastramqpi.config import Settings
from fastramqpi.main import FastRAMQPI
from fastramqpi.ramqp.config import AMQPConnectionSettings


@pytest.fixture(scope="session")
def monkeysession() -> Generator[MonkeyPatch, None, None]:
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture
def set_settings(
    monkeypatch: MonkeyPatch,
) -> Generator[Callable[..., None], None, None]:
    """Set settings via kwargs callback."""

    def _inner(**kwargs: Any) -> None:
        for key, value in kwargs.items():
            monkeypatch.setenv(key, value)

    yield _inner


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


@pytest.fixture(autouse=True, scope="session")
def disable_metrics(monkeysession: MonkeyPatch) -> Generator[None, None, None]:
    """Disable metrics by setting ENABLE_METRICS to false by default."""
    monkeysession.setenv("ENABLE_METRICS", "false")
    yield


@pytest.fixture(scope="session")
def enable_metrics(monkeysession: MonkeyPatch) -> Generator[None, None, None]:
    """Enable metrics by setting ENABLE_METRICS to true on demand."""
    monkeysession.setenv("ENABLE_METRICS", "true")
    yield


@pytest.fixture
def fastramqpi_builder(
    settings: Settings,
) -> Generator[Callable[[], FastRAMQPI], None, None]:
    """Fixture for generating FastRAMQPI instances."""
    # pylint: disable=unnecessary-lambda
    yield lambda: FastRAMQPI("test", settings=settings, graphql_version=20)


@pytest.fixture
def fastramqpi(
    fastramqpi_builder: Callable[[], FastRAMQPI],
) -> Generator[FastRAMQPI, None, None]:
    """Fixture for the FastRAMQPI instance."""
    yield fastramqpi_builder()


@pytest.fixture
def disable_amqp_lifespan(fastramqpi: FastRAMQPI) -> Generator[None, None, None]:
    fastramqpi._context["lifespan_managers"][1000].remove(fastramqpi.amqpsystem)
    yield


@pytest.fixture
def test_client_builder(
    fastramqpi: FastRAMQPI,
) -> Generator[Callable[[FastRAMQPI | None], TestClient], None, None]:
    """Fixture for generating FastRAMQPI / FastAPI test clients."""

    def create_test_client(override: FastRAMQPI | None = None) -> TestClient:
        app = fastramqpi.get_app()
        if override is not None:
            app = override.get_app()
        return TestClient(app)

    yield create_test_client


@pytest.fixture
def test_client(
    test_client_builder: Callable[[], TestClient],
) -> Generator[TestClient, None, None]:
    """Fixture for the FastAPI test client."""
    test_client = test_client_builder()
    with test_client:
        yield test_client


@pytest.fixture
def graphql_session() -> Generator[AsyncMock, None, None]:
    """Fixture for the GraphQL session."""
    yield AsyncMock()


@pytest.fixture
def model_client() -> Generator[AsyncMock, None, None]:
    """Fixture for the ModelClient."""
    yield AsyncMock()
