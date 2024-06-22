# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
# SPDX-License-Identifier: MPL-2.0
"""AMQP2HTTP bridge."""
from typing import Any

from fastapi import FastAPI
from pydantic import BaseSettings
from pydantic import Field

from fastramqpi.config import Settings as FastRAMQPISettings
from fastramqpi.main import FastRAMQPI
from fastramqpi.ramqp.depends import rate_limit
from fastramqpi.ramqp import Router
from fastapi import Depends
from typing import Awaitable

import asyncio
from functools import partial
from typing import Callable

import httpx
import structlog
from fastapi import status
from fastramqpi.ramqp.depends import Message
from fastramqpi.ramqp.utils import RejectMessage
from fastramqpi.ramqp.utils import RequeueMessage


logger = structlog.stdlib.get_logger()


class Settings(BaseSettings):
    class Config:
        frozen = True
        env_nested_delimiter = "__"

    fastramqpi: FastRAMQPISettings = Field(
        default_factory=FastRAMQPISettings, description="FastRAMQPI settings"
    )

    # TODO: Configurable parallelity?
    name: str
    integration_url: str
    event_mapping: dict[str, str]


async def process_amqp_message(
    endpoint_url: str,
    message: Message,
) -> None:
    async with httpx.AsyncClient() as client:
        headers = {}
        # TODO: Add more headers based on IncomingMessage as required
        if message.content_type is not None:
            headers["Content-Type"] = message.content_type
        if message.content_encoding is not None:
            headers["Content-Encoding"] = message.content_encoding
        if message.correlation_id is not None:
            headers["X-Correlation-ID"] = message.correlation_id
        if message.message_id is not None:
            headers["X-Message-ID"] = message.message_id
        for key, value in message.headers.items():
            headers[f"X-AMQP-HEADER-{key}"] = str(value)

        logger.info(
            "amqp-to-http request",
            endpoint_url=endpoint_url,
            content=message.body,
            headers=headers,
        )
        response = await client.post(
            endpoint_url, content=message.body, headers=headers
        )
        logger.info(
            "amqp-to-http response",
            status_code=response.status_code,
            content=response.content,
        )

        # Handle legal issues
        if response.status_code in [status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS]:
            logger.info("Integration requested us to reject the message")
            raise RejectMessage("We legally cannot process this")

        # Handle status-codes indicating that we may be going too fast
        if response.status_code in [
            status.HTTP_408_REQUEST_TIMEOUT,
            status.HTTP_425_TOO_EARLY,
            status.HTTP_429_TOO_MANY_REQUESTS,
            # TODO: Maybe only sleep on 503 if it is a redelivery?
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_504_GATEWAY_TIMEOUT,
        ]:
            # TODO: Maybe the response should contain the sleep time?
            logger.info("Integration requested us to slow down")
            await asyncio.sleep(30)
            raise RequeueMessage("Was going too fast")

        # All 200 status-codes are OK
        if 200 <= response.status_code < 300:
            logger.debug("Integration succesfully processed message")
            return

        # TODO: Do we want to reject or requeue this?
        if response.status_code in [status.HTTP_501_NOT_IMPLEMENTED]:
            logger.info("Integration notified us that the endpoint is not implemented")
            raise RequeueMessage("Not implemented")

        # Any 400 code means we need to reject the message
        # TODO: We should probably distinguish bad AMQP events from bad forwards?
        if 400 <= response.status_code < 500:
            # NOTE: All of these should probably be deadlettered in the future
            logger.info("Integration could not handle the request")
            raise RequeueMessage("We send a bad request")
        # Any other 500 code means we need to retry
        if 500 <= response.status_code < 600:
            logger.info("Integration could not handle the request")
            raise RequeueMessage("The server done goofed")

        # We intentionally do not handle 100 and 300 codes
        # If we got a 300 code it is probably a misconfiguration
        # NOTE: All of these should probably be deadlettered in the future
        logger.info("Integration send an unknown status-code", status_code=response.status_code)
        raise RequeueMessage(f"Unexpected status-code: {response.status_code}")


def amqp2http(
    url: str,
    name: str,
) -> Callable[[Message], Awaitable[None]]:
    callable = partial(process_amqp_message, url)
    callable.__name__ = name
    return callable


def create_fastramqpi(**kwargs: Any) -> FastRAMQPI:
    settings = Settings(**kwargs)

    amqp_router = Router()
    for routing_key, endpoint in settings.event_mapping.items():
        amqp_router.register(
            routing_key, dependencies=[Depends(rate_limit(10))]
        )(amqp2http(url=settings.integration_url + endpoint, name=routing_key))

    fastramqpi = FastRAMQPI(
        application_name="amqp2http_" + settings.name,
        settings=settings.fastramqpi,
        graphql_version=22,
    )
    fastramqpi.add_context(settings=settings)

    # Add our AMQP router(s)
    amqpsystem = fastramqpi.get_amqpsystem()
    amqpsystem.router.registry.update(amqp_router.registry)

    return fastramqpi


def create_app(**kwargs: Any) -> FastAPI:
    fastramqpi = create_fastramqpi(**kwargs)
    return fastramqpi.get_app()
