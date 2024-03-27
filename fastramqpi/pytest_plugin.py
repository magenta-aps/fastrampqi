# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio
import urllib.parse
from asyncio import CancelledError
from asyncio import create_task
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Any
from typing import NoReturn

import httpx
import pytest
from httpx import AsyncClient
from httpx import BasicAuth
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
                "amqp_queue_isolation",
                "passthrough_backing_services",
            ]


@pytest.fixture
def _settings() -> Any:
    """Access FastRAMQPI settings without coupling to the integration's settings."""
    # We must defer importing from the FastRAMQPI module till run-time.
    # https://github.com/pytest-dev/pytest-cov/issues/587
    from fastramqpi.config import Settings

    class _Settings(Settings):
        class Config:
            env_prefix = "FASTRAMQPI__"

    return _Settings()


@pytest.fixture
async def mo_client(_settings: Any) -> AsyncIterator[AsyncClient]:
    """HTTPX client with the OS2mo URL preconfigured."""
    async with httpx.AsyncClient(base_url=_settings.mo_url) as client:
        yield client


@pytest.fixture
async def rabbitmq_management_client(_settings: Any) -> AsyncIterator[AsyncClient]:
    """HTTPX client for the RabbitMQ management API."""
    amqp = _settings.amqp.get_url()
    async with httpx.AsyncClient(
        base_url=f"http://{amqp.host}:15672/api/",
        auth=BasicAuth(
            username=amqp.user,
            password=amqp.password,
        ),
    ) as client:
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
async def amqp_queue_isolation(
    rabbitmq_management_client: AsyncClient,
) -> None:
    """Ensure test isolation by deleting all AMQP queues before tests.

    Automatically used on tests marked as integration_test.
    """
    queues = (await rabbitmq_management_client.get("queues")).json()
    # vhost and name must be URL-encoded. This includes `/`, which is normally regarded
    # as safe. This is particularly important for the default AMQP vhost `/`.
    urls = (
        "queues/{vhost}/{name}".format(
            vhost=urllib.parse.quote(q["vhost"], safe=""),
            name=urllib.parse.quote(q["name"], safe=""),
        )
        for q in queues
    )
    deletes = [rabbitmq_management_client.delete(url) for url in urls]
    await asyncio.gather(*deletes)


@pytest.fixture
def passthrough_backing_services(_settings: Any, respx_mock: MockRouter) -> None:
    """Allow calls to the backing services to bypass the RESPX mocking.

    Automatically used on tests marked as integration_test.
    """
    # mo and keycloak are named to allow tests to revert the passthrough if needed
    respx_mock.route(name="keycloak", host=_settings.auth_server.host).pass_through()
    respx_mock.route(name="mo", host=_settings.mo_url.host).pass_through()
    # rabbitmq management
    respx_mock.route(host=_settings.amqp.get_url().host).pass_through()
    respx_mock.route(host="localhost").pass_through()
