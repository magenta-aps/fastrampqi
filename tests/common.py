# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
"""This module contains commonly used test utilities."""
import asyncio
import random
import string
from typing import Any
from typing import Dict
from typing import List

from aio_pika import IncomingMessage

from ramqp.abstract_amqpsystem import AbstractAMQPSystem


async def callback_func1(_: IncomingMessage) -> None:
    """Dummy callback method."""


async def callback_func2(_: IncomingMessage) -> None:
    """Dummy callback method."""


def random_string(length: int = 30) -> str:
    """Generate a random string of characters.

    Args:
        length: The desired length of the string

    Returns:
        A string of random numbers, upper- and lower-case letters.
    """
    return "".join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
        for _ in range(length)
    )


def _test_run_forever_worker(amqp_system: AbstractAMQPSystem) -> None:
    params: Dict[str, Any] = {}

    async def start(*_: List[Any], **__: Dict[str, Any]) -> None:
        # Instead of starting, shutdown the event-loop
        loop = asyncio.get_running_loop()
        loop.stop()

        params["start"] = True

    async def stop(*_: List[Any], **__: Dict[str, Any]) -> None:
        params["stop"] = True

    # mypy says: Cannot assign to a method, we ignore it
    amqp_system.start = start  # type: ignore
    amqp_system.stop = stop  # type: ignore
    amqp_system.run_forever()

    assert list(params.keys()) == ["start", "stop"]