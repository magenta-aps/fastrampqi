# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
# pylint: disable=protected-access
"""This module tests the Router.register decorator method."""

from typing import Any

import pytest
from aio_pika import IncomingMessage
from fastapi import Depends
from more_itertools import all_unique
from structlog.testing import LogCapture

from fastramqpi.ramqp import AMQPSystem
from fastramqpi.ramqp.utils import CallbackType
from fastramqpi.ramqp.utils import function_to_name

from .common import callback_func1
from .common import callback_func2


def get_registry(amqp_system: AMQPSystem) -> dict[CallbackType, set[str]]:
    """Extract the AMQPSystem callback registry.

    Args:
        amqp_system: The system to extract the registry from

    Returns:
        The callback registry.
    """
    return amqp_system.router.registry


def test_register(amqp_system: AMQPSystem, log_output: LogCapture) -> None:
    """Happy-path test.

    Tests that:
    * The decorator does not modify the callback.
    * The callback is added to the callback registry
    * Log outputs are as expected
    """
    # Call decorator on our function, and check that the function is not modified
    # The decorator should purely register the callback, not modify our function
    assert get_registry(amqp_system) == {}
    decorated_func = amqp_system.router.register("test.routing.key")(callback_func1)
    assert id(callback_func1) == id(decorated_func)

    # Check that the amqp system did not start, and that our function has been added
    assert amqp_system.started is False
    assert get_registry(amqp_system) == {callback_func1: {"test.routing.key"}}

    # Test that the call was logged
    assert log_output.entries == [
        {
            "routing_key": "test.routing.key",
            "function": "callback_func1",
            "event": "Register called",
            "log_level": "info",
        }
    ]


def test_register_invalid_routing_key(amqp_system: AMQPSystem) -> None:
    """Test that you cannot call register with an empty routing key."""
    # Cannot call register with empty routing key
    with pytest.raises(AssertionError):
        amqp_system.router.register("")(callback_func1)


def test_register_multiple(amqp_system: AMQPSystem) -> None:
    """Test that functions are added to the registry as expected."""
    assert get_registry(amqp_system) == {}

    amqp_system.router.register("test.routing.key")(callback_func1)
    assert get_registry(amqp_system) == {callback_func1: {"test.routing.key"}}

    amqp_system.router.register("test.routing.key")(callback_func1)
    assert get_registry(amqp_system) == {callback_func1: {"test.routing.key"}}

    amqp_system.router.register("test.routing.key2")(callback_func1)
    assert get_registry(amqp_system) == {
        callback_func1: {"test.routing.key", "test.routing.key2"}
    }

    amqp_system.router.register("test.routing.key")(callback_func2)
    assert get_registry(amqp_system) == {
        callback_func1: {"test.routing.key", "test.routing.key2"},
        callback_func2: {"test.routing.key"},
    }

    assert all_unique(map(function_to_name, get_registry(amqp_system).keys()))


def test_register_dependencies(amqp_system: AMQPSystem) -> None:
    """Test that functions get their dependencies attached."""
    assert get_registry(amqp_system) == {}

    async def callback_func3(_: IncomingMessage, **__: Any) -> None:
        """Dummy callback method."""

    def sync_deps() -> int:
        return 37

    def async_deps() -> int:
        return 7

    dependencies = [Depends(sync_deps), Depends(async_deps)]

    decorated_func = amqp_system.router.register(
        "test.routing.key", dependencies=dependencies
    )(callback_func3)
    assert id(callback_func3) == id(decorated_func)
    assert getattr(callback_func3, "dependencies", []) == dependencies

    assert get_registry(amqp_system) == {callback_func3: {"test.routing.key"}}
