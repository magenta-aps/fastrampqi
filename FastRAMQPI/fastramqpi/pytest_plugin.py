# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio
from asyncio import CancelledError
from asyncio import create_task
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import NoReturn

import httpx
import pytest
from httpx import AsyncClient
from pytest import Config
from pytest import Item
from respx import MockRouter


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        "markers", "integration_test: mark test as an integration test."
    )


def pytest_collection_modifyitems(items: list[Item]) -> None:
    """Automatically use convenient fixtures for tests marked with integration_test."""

    for item in items:
        if item.get_closest_marker("integration_test"):
            # MUST prepend to replicate auto-use fixtures coming first
            item.fixturenames[:0] = [  # type: ignore[attr-defined]
                "amqp_event_emitter",
                "database_snapshot_and_restore",
                "passthrough_backing_services",
            ]


@pytest.fixture
async def mo_client() -> AsyncIterator[AsyncClient]:
    """HTTPX client with the OS2mo URL preconfigured."""
    async with httpx.AsyncClient(base_url="http://mo:5000") as client:
        yield client


@pytest.fixture
async def amqp_event_emitter(mo_client: AsyncClient) -> AsyncIterator[None]:
    """Continuously, and quickly, emit OS2mo AMQP events during tests.

    Normally, OS2mo emits AMQP events periodically, but very slowly. Even though there
    are no guarantees as to message delivery speed, and we therefore should not design
    our system around such expectation, waiting a long time for tests to pass in the
    pipelines - or to fail during development - is a very poor development experience.

    Automatically used on tests marked as integration_test.
    """

    async def emitter() -> NoReturn:
        while True:
            await asyncio.sleep(3)
            r = await mo_client.post("/testing/amqp/emit")
            r.raise_for_status()

    task = create_task(emitter())
    yield
    task.cancel()
    with suppress(CancelledError):
        # Await the task to ensure potential errors in the fixture itself, such as a
        # wrong URL or misconfigured OS2mo, are returned to the user.
        await task


@pytest.fixture
async def database_snapshot_and_restore(mo_client: AsyncClient) -> AsyncIterator[None]:
    """Ensure test isolation by resetting the OS2mo database between tests.

    Automatically used on tests marked as integration_test.
    """
    r = await mo_client.post("/testing/database/snapshot")
    r.raise_for_status()
    yield
    r = await mo_client.post("/testing/database/restore")
    r.raise_for_status()


@pytest.fixture
def passthrough_backing_services(respx_mock: MockRouter) -> None:
    """Allow calls to the backing services to bypass the RESPX mocking.

    Automatically used on tests marked as integration_test.
    """
    respx_mock.route(name="keycloak", host="keycloak").pass_through()
    respx_mock.route(name="mo", host="mo").pass_through()
    respx_mock.route(host="localhost").pass_through()
