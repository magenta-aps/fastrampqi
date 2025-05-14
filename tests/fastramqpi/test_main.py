# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=protected-access
# pylint: disable=unused-argument
"""Test the FastRAMQPI system."""

from contextlib import asynccontextmanager
from functools import partial
from typing import AsyncIterator
from typing import Callable
from typing import Generator
from unittest.mock import ANY
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import AnyHttpUrl
from pydantic import SecretStr
from pydantic import parse_obj_as
from pytest import MonkeyPatch

from fastramqpi import depends
from fastramqpi.config import Settings
from fastramqpi.context import Context
from fastramqpi.main import FastRAMQPI
from fastramqpi.main import construct_legacy_clients
from fastramqpi.metrics import dipex_last_success_timestamp
from fastramqpi.ramqp.mo import MOAMQPSystem


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


@pytest.mark.usefixtures("disable_amqp_lifespan")
def test_root_endpoint(test_client: TestClient) -> None:
    """Test the root endpoint on our app."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"name": "test"}


@pytest.mark.usefixtures("disable_amqp_lifespan", "enable_metrics")
def test_metrics_endpoint(fastramqpi: FastRAMQPI, test_client: TestClient) -> None:
    """Test the metrics endpoint on our app."""
    response = test_client.get("/metrics")
    assert response.status_code == 200
    assert "# TYPE build_information_info gauge" in response.text


@pytest.mark.usefixtures("disable_amqp_lifespan", "enable_metrics")
def test_metrics_dipex_last_success_timestamp(
    fastramqpi: FastRAMQPI, test_client: TestClient
) -> None:
    """Test that dipex_last_success_timestamp can be set."""
    response = test_client.get("/metrics")
    assert "dipex_last_success_timestamp_seconds 0.0" in response.text

    dipex_last_success_timestamp.set_to_current_time()

    response = test_client.get("/metrics")
    # Stops working 2033-05-18T03:33:20+00:00. Apologies from the past!
    assert "dipex_last_success_timestamp_seconds 1" in response.text


@pytest.mark.parametrize("endpoint", ["/health/ready", "/health/live"])
def test_liveness_endpoint_healthy(
    fastramqpi: FastRAMQPI,
    test_client_builder: Callable[..., TestClient],
    endpoint: str,
) -> None:
    """Test that the liveness endpoint returns 204 if everything is ok."""
    amqp_system = MagicMock()
    amqp_system.healthcheck.return_value = True

    fastramqpi._context["amqpsystem"] = amqp_system
    fastramqpi._context["lifespan_managers"] = {}

    test_client = test_client_builder(fastramqpi)

    with test_client:
        response = test_client.get(endpoint)
        assert response.status_code == 200
        assert amqp_system.mock_calls == [call.healthcheck()]
        assert response.json() == {
            "AMQP": True,
        }


@pytest.mark.parametrize("endpoint", ["/health/ready", "/health/live"])
def test_liveness_endpoint_unhealthy(
    fastramqpi: FastRAMQPI,
    test_client_builder: Callable[..., TestClient],
    endpoint: str,
) -> None:
    """Test that the liveness endpoint handles exceptions nicely."""
    amqp_system = MagicMock()
    amqp_system.healthcheck.side_effect = ValueError("BOOM")

    fastramqpi._context["amqpsystem"] = amqp_system
    fastramqpi._context["lifespan_managers"] = {}

    test_client = test_client_builder(fastramqpi)

    with test_client:
        response = test_client.get(endpoint)
        assert response.status_code == 503
        assert amqp_system.mock_calls == [call.healthcheck()]
        assert response.json() == {
            "AMQP": False,
        }


@patch("fastramqpi.main.LegacyGraphQLClient")
def test_legacy_gql_client_created_with_timeout(
    mock_gql_client: MagicMock, settings: Settings
) -> None:
    """Test that the LegacyGraphQLClient is called with timeout setting"""

    # Arrange
    settings = settings.copy(
        update=dict(
            graphql_timeout=15,
        )
    )

    # Act
    construct_legacy_clients(graphql_version=20, settings=settings)

    # Assert
    assert mock_gql_client.call_args.kwargs["httpx_client_kwargs"]["timeout"] == 15
    assert mock_gql_client.call_args.kwargs["execute_timeout"] == 15


def test_mo_client(settings: Settings, monkeypatch: MonkeyPatch) -> None:
    """Test that the MO client is called with the correct settings."""
    mock_client = MagicMock()
    monkeypatch.setattr("fastramqpi.main.AsyncOAuth2Client", mock_client)

    settings = settings.copy(
        update=dict(
            client_id="foo",
            client_secret=SecretStr("bar"),
            auth_server=parse_obj_as(AnyHttpUrl, "https://keycloak.example.org"),
            auth_realm="os2mo",
            graphql_timeout=15,
        )
    )

    FastRAMQPI(application_name="test", settings=settings, graphql_version=20)

    mock_client.assert_called_once_with(
        base_url="http://mo-service:5000",
        client_id="foo",
        client_secret="bar",
        grant_type="client_credentials",
        token_endpoint="https://keycloak.example.org/realms/os2mo/protocol/openid-connect/token",
        token={"expires_at": -1, "access_token": ""},
        timeout=15,
    )


async def test_graphql_client(settings: Settings, monkeypatch: MonkeyPatch) -> None:
    """Test that the GraphQL client is initialised correctly."""
    monkeypatch.setattr("fastramqpi.main.MOAMQPSystem", MagicMock())
    cls = MagicMock()

    app = FastRAMQPI(
        application_name="test",
        settings=settings,
        graphql_version=2000,
        graphql_client_cls=cls,
    ).get_app()
    with TestClient(app):
        pass

    cls.assert_called_once_with(
        url="http://mo-service:5000/graphql/v2000",
        http_client=ANY,
    )
    assert isinstance(cls.call_args.kwargs["http_client"], AsyncOAuth2Client)


def test_get_app(fastramqpi: FastRAMQPI) -> None:
    """Test that get_app returns a FastAPI application."""
    app = fastramqpi.get_app()
    assert isinstance(app, FastAPI)


def test_get_context(fastramqpi: FastRAMQPI) -> None:
    """Test that get_context returns our context."""
    context = fastramqpi.get_context()
    assert isinstance(context, dict)
    assert isinstance(context["app"], FastAPI)


def test_get_amqpsystem(fastramqpi: FastRAMQPI) -> None:
    """Test that get_amqpsystem returns a MOAMQPSystem."""
    amqpsystem = fastramqpi.get_amqpsystem()
    assert isinstance(amqpsystem, MOAMQPSystem)


def test_add_context(fastramqpi: FastRAMQPI) -> None:
    """Test that add_context adds to the user_context."""
    assert fastramqpi._context["user_context"] == {}

    fastramqpi.add_context(key1="value1")
    assert fastramqpi._context["user_context"] == {
        "key1": "value1",
    }

    fastramqpi.add_context(key1="value2")
    assert fastramqpi._context["user_context"] == {
        "key1": "value2",
    }

    fastramqpi.add_context(key2="value2")
    assert fastramqpi._context["user_context"] == {
        "key1": "value2",
        "key2": "value2",
    }


def dummy_healthcheck(context: Context) -> bool:
    """Dummy healthcheck implementation."""
    return True


def test_add_healthcheck(fastramqpi: FastRAMQPI) -> None:
    """Test that add_healthcheck adds to the healthcheck list."""
    assert fastramqpi.app.state.healthchecks.keys() == {
        "AMQP",
    }

    fastramqpi.add_healthcheck(
        name="Test",
        # The type is perfectly in order, but mypy cannot handle recursive types
        healthcheck=dummy_healthcheck,  # type: ignore
    )

    assert fastramqpi.app.state.healthchecks.keys() == {
        "AMQP",
        "Test",
    }
    # pylint: disable=comparison-with-callable
    assert fastramqpi.app.state.healthchecks["Test"] == dummy_healthcheck

    with pytest.raises(ValueError) as excinfo:
        fastramqpi.add_healthcheck(
            name="Test",
            # The type is perfectly in order, but mypy cannot handle recursive types
            healthcheck=dummy_healthcheck,  # type: ignore
        )
    assert "Name already used" in str(excinfo.value)


@asynccontextmanager
async def dummy_lifespan_manager() -> AsyncIterator[None]:
    """Dummy lifespan manager implementation."""
    yield


def test_add_lifespan_manager(fastramqpi: FastRAMQPI) -> None:
    """Test that add_lifespan_manager adds to the lifespan manager list."""
    assert fastramqpi._context["lifespan_managers"].keys() == {100, 300, 400, 1000}
    # We expect LegacyGraphQLClient, LegacyModelClient, AsyncOAuth2Client MO client and
    # RAMQP to be present.
    assert len(fastramqpi._context["lifespan_managers"][100]) == 1
    assert len(fastramqpi._context["lifespan_managers"][300]) == 1
    assert len(fastramqpi._context["lifespan_managers"][400]) == 1
    assert len(fastramqpi._context["lifespan_managers"][1000]) == 1

    context_manager = dummy_lifespan_manager()

    fastramqpi.add_lifespan_manager(context_manager)
    assert fastramqpi._context["lifespan_managers"].keys() == {100, 300, 400, 1000}
    # We expect our manager to have been added
    assert len(fastramqpi._context["lifespan_managers"][100]) == 1
    assert len(fastramqpi._context["lifespan_managers"][300]) == 1
    assert len(fastramqpi._context["lifespan_managers"][400]) == 1
    assert len(fastramqpi._context["lifespan_managers"][1000]) == 2

    fastramqpi.add_lifespan_manager(context_manager, priority=1)
    assert fastramqpi._context["lifespan_managers"].keys() == {1, 100, 300, 400, 1000}
    # We expect our manager to have been added
    assert len(fastramqpi._context["lifespan_managers"][1]) == 1

    fastramqpi.add_lifespan_manager(context_manager, priority=1)
    assert fastramqpi._context["lifespan_managers"].keys() == {1, 100, 300, 400, 1000}
    # We expect our manager already exist, and not to have been readded
    assert len(fastramqpi._context["lifespan_managers"][1]) == 1


async def test_lifespan_manager_execution(fastramqpi: FastRAMQPI) -> None:
    """Test that ASGI life-management triggers our lifespan managers."""
    fastramqpi._context["lifespan_managers"] = {}

    events = []

    @asynccontextmanager
    async def test_lifespan_manager(i: int) -> AsyncIterator[None]:
        events.append((i, "entered"))
        yield
        events.append((i, "exited"))

    # Register 3 callbacks of different priorities
    for priority in range(3):
        fastramqpi.add_lifespan_manager(
            partial(test_lifespan_manager, priority)(), priority=priority
        )

    # Assert they have not run at all
    assert not events

    app = fastramqpi.get_app()

    with TestClient(app):
        assert events == [
            (0, "entered"),
            (1, "entered"),
            (2, "entered"),
        ]

    assert events == [
        (0, "entered"),
        (1, "entered"),
        (2, "entered"),
        (2, "exited"),
        (1, "exited"),
        (0, "exited"),
    ]


@patch("fastramqpi.main.MOAMQPSystem")
async def test_default_lifespan_manager(
    MOAMQPSystem: MagicMock,  # pylint: disable=invalid-name
    fastramqpi_builder: Callable[[], FastRAMQPI],
    test_client_builder: Callable[[FastRAMQPI | None], TestClient],
) -> None:
    """Test the default FastRAMQPI lifespan managers."""

    fastramqpi = fastramqpi_builder()
    mock = AsyncMock()
    fastramqpi._context["legacy_graphql_client"] = mock

    mock.__aenter__.assert_not_called()
    with test_client_builder(fastramqpi):
        mock.__aenter__.assert_called_once()
        mock.__aexit__.assert_not_called()
    mock.__aexit__.assert_called_once()


@patch("fastramqpi.main.MOAMQPSystem")
async def test_context(
    MOAMQPSystem: MagicMock,  # pylint: disable=invalid-name
    fastramqpi_builder: Callable[[], FastRAMQPI],
    test_client_builder: Callable[[FastRAMQPI | None], TestClient],
) -> None:
    """Test the default FastRAMQPI lifespan managers."""

    fastramqpi = fastramqpi_builder()
    fastramqpi.add_context(a=1)
    app = fastramqpi.get_app()

    @app.get("/test")
    async def test(user_context: depends.UserContext) -> dict:
        return user_context

    with test_client_builder(fastramqpi) as client:
        assert client.get("/test").json() == {"a": 1}
