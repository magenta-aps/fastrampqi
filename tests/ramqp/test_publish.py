# SPDX-FileCopyrightText: 2023-2023 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
"""This module tests the AMQPSystem.publish_message method."""
import asyncio
from collections.abc import Callable

import pytest
from pydantic import AmqpDsn
from pydantic import parse_obj_as

from .common import random_string
from fastramqpi.ramqp import AMQPSystem
from fastramqpi.ramqp.config import AMQPConnectionSettings


@pytest.mark.integration_test
async def test_publish_exchange(amqp_test: Callable) -> None:
    """Test that messages can be published to a specific exchange."""
    test_id = random_string()
    exchange_1 = f"{test_id}_exchange_1"
    exchange_2 = f"{test_id}_exchange_2"
    routing_key = "test.routing.key"

    amqp_system_1 = AMQPSystem(
        settings=AMQPConnectionSettings(
            url=parse_obj_as(AmqpDsn, "amqp://guest:guest@msg-broker:5672"),
            queue_prefix=exchange_1,
            exchange=exchange_1,
        ),
    )
    amqp_system_2 = AMQPSystem(
        settings=AMQPConnectionSettings(
            url=parse_obj_as(AmqpDsn, "amqp://guest:guest@msg-broker:5672"),
            queue_prefix=exchange_2,
            exchange=exchange_2,
        ),
    )

    calls: dict[int, bool] = {}

    @amqp_system_1.router.register(routing_key)
    async def callback_1() -> None:
        calls[1] = True

    @amqp_system_2.router.register(routing_key)
    async def callback_2() -> None:
        calls[2] = True

    async with amqp_system_1, amqp_system_2:
        await amqp_system_1.publish_message(
            routing_key=routing_key,
            payload="hello",
            exchange=exchange_2,
        )
        await asyncio.sleep(1)

    assert calls.get(1) is None
    assert calls.get(2) is True


@pytest.mark.integration_test
async def test_publish_to_queue(amqp_test: Callable) -> None:
    """Test that messages can be published to a specific queue."""
    test_id = random_string()
    exchange = f"{test_id}_exchange"
    routing_key = "test"

    amqp_system = AMQPSystem(
        settings=AMQPConnectionSettings(
            url=parse_obj_as(AmqpDsn, "amqp://guest:guest@msg-broker:5672"),
            queue_prefix=exchange,
            exchange=exchange,
        ),
    )

    calls: dict[int, bool] = {}

    @amqp_system.router.register(routing_key)
    async def callback_1() -> None:
        calls[1] = True

    @amqp_system.router.register(routing_key)
    async def callback_2() -> None:
        calls[2] = True

    async with amqp_system:
        await amqp_system.publish_message_to_queue(
            queue=f"{exchange}_callback_1",
            payload="hello",
        )
        await asyncio.sleep(1)

    # Message should only be seen by callback_1 even though both callbacks listen to the
    # same routing-key, the same exchange and the same AMQPSystem
    assert calls.get(1) is True
    assert calls.get(2) is None
