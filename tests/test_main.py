# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=protected-access
# pylint: disable=unused-argument
"""Test the FastRAMQPI system."""
from contextlib import asynccontextmanager
from functools import partial
from typing import Any
from typing import AsyncIterator
from typing import Callable
from typing import cast
from typing import Set
from typing import Tuple
from unittest.mock import AsyncMock
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from fastapi.testclient import TestClient
from ramqp.mo import MOAMQPSystem

from fastramqpi.config import Settings
from fastramqpi.context import Context
from fastramqpi.main import build_information
from fastramqpi.main import construct_clients
from fastramqpi.main import FastRAMQPI
from fastramqpi.main import update_build_information


def get_metric_value(metric: Any, labels: Tuple[str]) -> float:
    """Get the value of a given metric with the given label-set.

    Args:
        metric: The metric to query.
        labels: The label-set to query with.

    Returns:
        The metric value.
    """
    metric = metric.labels(*labels)._value
    return cast(float, metric.get())


def clear_metric_value(metric: Any) -> None:
    """Get the value of a given metric with the given label-set.

    Args:
        metric: The metric to query.

    Returns:
        The metric value.
    """
    metric.clear()


def get_metric_labels(metric: Any) -> Set[Tuple[str]]:
    """Get the label-set for a given metric.

    Args:
        metric: The metric to query.

    Returns:
        The label-set.
    """
    return set(metric._metrics.keys())


def test_build_information() -> None:
    """Test that build metrics are updated as expected."""
    clear_metric_value(build_information)
    assert build_information._value == {}
    update_build_information("1.0.0", "cafebabe")
    assert build_information._value == {
        "version": "1.0.0",
        "hash": "cafebabe",
    }


def test_root_endpoint(test_client: TestClient) -> None:
    """Test the root endpoint on our app."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"name": "test"}


def test_metrics_endpoint(
    enable_metrics: None, test_client_builder: Callable[[], TestClient]
) -> None:
    """Test the metrics endpoint on our app."""
    test_client = test_client_builder()
    response = test_client.get("/metrics")
    assert response.status_code == 200
    assert "# TYPE build_information_info gauge" in response.text


def test_liveness_endpoint(test_client: TestClient) -> None:
    """Test the liveness endpoint on our app."""
    response = test_client.get("/health/live")
    assert response.status_code == 204


@pytest.mark.parametrize(
    "amqp_ok,gql_ok,model_ok,expected",
    [
        (True, True, True, 204),
        (False, True, True, 503),
        (True, False, True, 503),
        (True, True, False, 503),
        (True, False, False, 503),
        (False, True, False, 503),
        (False, False, True, 503),
        (False, False, False, 503),
    ],
)
def test_readiness_endpoint(
    fastramqpi: FastRAMQPI,
    graphql_session: AsyncMock,
    model_client: AsyncMock,
    test_client_builder: Callable[..., TestClient],
    amqp_ok: bool,
    gql_ok: bool,
    model_ok: bool,
    expected: int,
) -> None:
    """Test the readiness endpoint handles errors."""
    amqp_system = MagicMock()
    amqp_system.healthcheck.return_value = amqp_ok

    graphql_response = {}
    if gql_ok:
        graphql_response = {"org": {"uuid": "hello"}}
    else:
        graphql_response = {"org": {"uuid": False}}  # type: ignore
    graphql_session.execute.return_value = graphql_response

    model_response = MagicMock()
    if model_ok:
        model_response.json.return_value = [{"uuid": "hello"}]
    else:
        model_response.json.return_value = []
    model_client.get.return_value = model_response

    fastramqpi._context["amqpsystem"] = amqp_system
    fastramqpi._context["graphql_session"] = graphql_session
    fastramqpi._context["model_client"] = model_client
    test_client = test_client_builder(fastramqpi)

    response = test_client.get("/health/ready")
    assert response.status_code == expected
    assert amqp_system.mock_calls == [call.healthcheck()]


@pytest.mark.parametrize(
    "amqp_ok,gql_ok,model_ok,expected",
    [
        (True, True, True, 204),
        (False, True, True, 503),
        (True, False, True, 503),
        (True, True, False, 503),
        (True, False, False, 503),
        (False, True, False, 503),
        (False, False, True, 503),
        (False, False, False, 503),
    ],
)
def test_readiness_endpoint_exception(
    fastramqpi: FastRAMQPI,
    graphql_session: AsyncMock,
    model_client: MagicMock,
    test_client_builder: Callable[..., TestClient],
    amqp_ok: bool,
    gql_ok: bool,
    model_ok: bool,
    expected: int,
) -> None:
    """Test the readiness endpoint handled exceptions nicely."""
    amqp_system = MagicMock()
    if amqp_ok:
        amqp_system.healthcheck.return_value = True
    else:
        amqp_system.healthcheck.side_effect = ValueError("BOOM")

    graphql_response = {}
    if gql_ok:
        graphql_response = {"org": {"uuid": "hello"}}
    graphql_session.execute.return_value = graphql_response

    model_response = MagicMock()
    if model_ok:
        model_response.json.return_value = [{"uuid": "hello"}]
    else:
        model_response.side_effect = ValueError("boom")
    model_client.get.return_value = model_response

    fastramqpi._context["amqpsystem"] = amqp_system
    fastramqpi._context["graphql_session"] = graphql_session
    fastramqpi._context["model_client"] = model_client
    test_client = test_client_builder(fastramqpi)

    response = test_client.get("/health/ready")
    assert response.status_code == expected


@patch("fastramqpi.main.GraphQLClient")
def test_gql_client_created_with_timeout(mock_gql_client: MagicMock) -> None:
    """Test that GraphQLClient is called with timeout setting"""

    # Arrange
    settings = Settings(graphql_timeout=15)

    # Act
    construct_clients(settings)

    # Assert
    assert 15 == mock_gql_client.call_args.kwargs["httpx_client_kwargs"]["timeout"]
    assert 15 == mock_gql_client.call_args.kwargs["execute_timeout"]


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
    assert fastramqpi._context["healthchecks"].keys() == {
        "AMQP",
        "GraphQL",
        "Service API",
    }

    fastramqpi.add_healthcheck(
        name="Test",
        # The type is perfectly in order, but mypy cannot handle recursive types
        healthcheck=dummy_healthcheck,  # type: ignore
    )

    assert fastramqpi._context["healthchecks"].keys() == {
        "AMQP",
        "GraphQL",
        "Service API",
        "Test",
    }
    # pylint: disable=comparison-with-callable
    assert fastramqpi._context["healthchecks"]["Test"] == dummy_healthcheck

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
    assert fastramqpi._context["lifespan_managers"].keys() == {1000}
    # We expect GQL, ModelClient and RAMQP to be present
    assert len(fastramqpi._context["lifespan_managers"][1000]) == 3

    context_manager = dummy_lifespan_manager()

    fastramqpi.add_lifespan_manager(context_manager)
    assert fastramqpi._context["lifespan_managers"].keys() == {1000}
    # We expect our manager to have been added
    assert len(fastramqpi._context["lifespan_managers"][1000]) == 4

    fastramqpi.add_lifespan_manager(context_manager, priority=1)
    assert fastramqpi._context["lifespan_managers"].keys() == {1, 1000}
    # We expect our manager to have been added
    assert len(fastramqpi._context["lifespan_managers"][1]) == 1

    fastramqpi.add_lifespan_manager(context_manager, priority=1)
    assert fastramqpi._context["lifespan_managers"].keys() == {1, 1000}
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

    async with LifespanManager(app):
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
) -> None:
    """Test the default FastRAMQPI lifespan managers."""

    fastramqpi = fastramqpi_builder()
    fastramqpi._context["graphql_client"] = AsyncMock()
    # fastramqpi._context["model_client"] = AsyncMock()

    app = fastramqpi.get_app()
    async with LifespanManager(app):
        pass
