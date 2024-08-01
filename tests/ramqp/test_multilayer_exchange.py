# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
"""This module tests the migration to quorum queues."""
import asyncio
from uuid import uuid4

import pytest
from pydantic import AmqpDsn
from pydantic import parse_obj_as

from .common import random_string
from fastramqpi.ramqp import AMQPSystem
from fastramqpi.ramqp.config import AMQPConnectionSettings


@pytest.mark.integration_test
async def test_multilayer_exchange_publish() -> None:
    """Test that we can publish to different layers on the exchange."""
    url_raw = "amqp://guest:guest@msg-broker:5672"
    url = parse_obj_as(AmqpDsn, url_raw)

    mo_exchange = random_string()

    amqp_system_1 = AMQPSystem(
        settings=AMQPConnectionSettings(
            url=url,
            queue_prefix=random_string(),
            exchange=random_string(),
            upstream_exchange=mo_exchange,
        ),
    )

    amqp_system_2 = AMQPSystem(
        settings=AMQPConnectionSettings(
            url=url,
            queue_prefix=random_string(),
            exchange=random_string(),
            upstream_exchange=mo_exchange,
        ),
    )

    mo_amqp_system = AMQPSystem(
        settings=AMQPConnectionSettings(
            url=url,
            exchange=mo_exchange,
        ),
    )

    callback_1_event = asyncio.Event()

    async def callback_1() -> None:
        callback_1_event.set()

    callback_2_event = asyncio.Event()

    async def callback_2() -> None:
        callback_2_event.set()

    routing_key = "facet"
    payload = uuid4()

    amqp_system_1.router.register(routing_key)(callback_1)
    amqp_system_2.router.register(routing_key)(callback_2)

    async with mo_amqp_system, amqp_system_1, amqp_system_2:
        # Publishing to the OS2mo exchange to trigger both callbacks
        callback_1_event.clear()
        callback_2_event.clear()
        await mo_amqp_system.publish_message(routing_key, payload)
        await asyncio.wait_for(callback_1_event.wait(), timeout=1)
        await asyncio.wait_for(callback_2_event.wait(), timeout=1)

        # Publishing to the amqp_system_1 exchange to trigger one callback
        callback_1_event.clear()
        callback_2_event.clear()
        await mo_amqp_system.publish_message(
            routing_key, payload, exchange=amqp_system_1.exchange_name
        )
        await asyncio.wait_for(callback_1_event.wait(), timeout=1)
        assert callback_2_event.is_set() is False

        # Publishing to the amqp_system_2 exchange to trigger one callback
        callback_1_event.clear()
        callback_2_event.clear()
        await mo_amqp_system.publish_message(
            routing_key, payload, exchange=amqp_system_2.exchange_name
        )
        await asyncio.sleep(0)
        await asyncio.wait_for(callback_2_event.wait(), timeout=1)
        assert callback_1_event.is_set() is False
