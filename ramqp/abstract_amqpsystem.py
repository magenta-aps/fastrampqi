# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
# pylint: disable=too-few-public-methods
"""This module contains the Abstract AMQPSystem."""
import asyncio
import json
from abc import ABCMeta
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from functools import partial
from types import TracebackType
from typing import Any
from typing import Dict
from typing import Optional
from typing import Set
from typing import Type
from typing import TypeVar

import structlog
from aio_pika import connect_robust
from aio_pika import ExchangeType
from aio_pika import IncomingMessage
from aio_pika import Message
from aio_pika.abc import AbstractChannel
from aio_pika.abc import AbstractExchange
from aio_pika.abc import AbstractQueue
from aio_pika.abc import AbstractRobustConnection
from more_itertools import all_unique

from .config import ConnectionSettings
from .metrics import _handle_publish_metrics
from .metrics import _handle_receive_metrics
from .metrics import _setup_periodic_metrics
from .metrics import callbacks_registered
from .metrics import reconnect_counter
from .metrics import routes_bound
from .utils import CallbackType
from .utils import function_to_name

# Workaround until Self Types in Python 3.11 (PEP673)
TAMQPSystem = TypeVar("TAMQPSystem", bound="AbstractAMQPSystem")

logger = structlog.get_logger()


def reconnect_callback(_: AbstractRobustConnection) -> None:
    """Reconnect callback to update reconnect counter metric.

    Args:
        Unused connection

    Returns:
        None
    """
    reconnect_counter.inc()  # pragma: no cover


class AbstractAMQPRouter:
    """Abstract base-class for AMQPRouters.

    Shared code used by both AMQPRouter and MOAMQPRouter.
    """

    def __init__(self) -> None:
        self.registry: Dict[CallbackType, Set[str]] = {}

    def _register(self, routing_key: str) -> Callable[[CallbackType], CallbackType]:
        """Get a decorator for registering callbacks.

        Examples:
            ```
            address_create_decorator = router.register("EMPLOYEE.ADDRESS.CREATE")

            @address_create_decorator
            def callback1(message: IncomingMessage):
                pass

            @address_create_decorator
            def callback2(message: IncomingMessage):
                pass
            ```
            Or directly:
            ```
            @router.register("EMPLOYEE.ADDRESS.CREATE")
            def callback1(message: IncomingMessage):
                pass

            @router.register("EMPLOYEE.ADDRESS.CREATE")
            def callback2(message: IncomingMessage):
                pass
            ```

        Args:
            routing_key: The routing key to bind messages for.

        Returns:
            A decorator for registering a function to receive callbacks.
        """
        assert routing_key != ""

        def decorator(function: CallbackType) -> CallbackType:
            """Registers the given callback and routing key in the callback registry.

            Args:
                function: The callback to registry.

            Returns:
                The unmodified given function.
            """
            function_name = function_to_name(function)

            log = logger.bind(routing_key=routing_key, function=function_name)
            log.info("Register called")

            callbacks_registered.labels(routing_key).inc()
            self.registry.setdefault(function, set()).add(routing_key)
            return function

        return decorator


# pylint: disable=too-many-instance-attributes
class AbstractAMQPSystem(AbstractAsyncContextManager):
    """Abstract base-class for AMQPSystems.

    Shared code used by both AMQPSystem and MOAMQPSystem.
    """

    __metaclass__ = ABCMeta
    router_cls = AbstractAMQPRouter

    def __init__(
        self, *args: Any, **kwargs: Any
    ) -> None:  # TODO: Take settings, context, router
        self.settings = ConnectionSettings(*args, **kwargs)
        self.context: dict = {}
        self.router = self.router_cls()

        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractChannel] = None
        self._exchange: Optional[AbstractExchange] = None
        self._queues: Dict[str, AbstractQueue] = {}

        self._periodic_task: Optional[asyncio.Task] = None

    @property
    def started(self) -> bool:
        """Whether a connection has been made.

        Returns:
            Whether a connection has been made.
        """
        return self._connection is not None

    def healthcheck(self) -> bool:
        """Whether the system is running, alive and well

        Returns:
            Whether the system is running, alive and well
        """
        return (
            self._connection is not None
            and self._connection.is_closed is False
            and self._channel is not None
            and self._channel.is_closed is False
            and self._channel.is_initialized
        )

    async def start(self) -> None:
        """Start the AMQPSystem.

        This method:
        * Connects to the AMQP server.
        * Sets up the AMQP exchange if it does not exist
        * Creates durable queues for each callback in the callback registry.
        * Binds routes to the queues according to the callback registry.
        * Setups up periodic metrics.

        Returns:
            None
        """
        settings = self.settings

        # We expect no active connections to be established
        assert self._connection is None
        assert self._channel is None
        assert self._exchange is None

        # We expect function_to_name to be unique for each callback
        assert all_unique(map(function_to_name, self.router.registry.keys()))

        # We expect amqp_queue_prefix to be set if any callbacks are registered
        if self.router.registry:
            assert settings.amqp_queue_prefix is not None

        logger.info(
            "Establishing AMQP connection",
            scheme=settings.amqp_url.scheme,
            user=settings.amqp_url.user,
            host=settings.amqp_url.host,
            port=settings.amqp_url.port,
            path=settings.amqp_url.path,
        )
        self._connection = await connect_robust(settings.amqp_url)
        self._connection.reconnect_callbacks.add(reconnect_callback)

        logger.info("Creating AMQP channel")
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

        logger.info(
            "Attaching AMQP exchange to channel", exchange=settings.amqp_exchange
        )
        # Make our exchange durable so it survives broker restarts
        self._exchange = await self._channel.declare_exchange(
            settings.amqp_exchange, ExchangeType.TOPIC, durable=True
        )

        # TODO: Create queues and binds in parallel?
        self._queues = {}
        for callback, routing_keys in self.router.registry.items():
            function_name = function_to_name(callback)
            log = logger.bind(function=function_name)

            queue_name = f"{settings.amqp_queue_prefix}_{function_name}"
            log.info("Declaring unique message queue", queue_name=queue_name)
            # Make our queues durable so they survive broker restarts
            queue = await self._channel.declare_queue(queue_name, durable=True)
            self._queues[function_name] = queue

            log.info("Starting message listener")
            await queue.consume(partial(self._on_message, callback))

            log.info("Binding routing keys")
            for routing_key in routing_keys:
                log.info("Binding routing-key", routing_key=routing_key)
                await queue.bind(self._exchange, routing_key=routing_key)
                routes_bound.labels(function_name).inc()

        self._periodic_task = _setup_periodic_metrics(self._queues)

    async def stop(self) -> None:
        """Stop the AMQPSystem.

        This method disconnects from the AMQP server, and stops the periodic metrics.

        Returns:
            None
        """
        if self._periodic_task is not None:
            self._periodic_task.cancel()
            self._periodic_task = None

        self._exchange = None

        if self._channel is not None:
            await self._channel.close()
            self._channel = None

        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def __aenter__(self: TAMQPSystem) -> TAMQPSystem:
        """Start the AMQPSystem.

        Returns: Self.
        """
        await self.start()
        return await super().__aenter__()  # type: ignore[no-any-return]

    async def __aexit__(
        self,
        __exc_type: Optional[Type[BaseException]],
        __exc_value: Optional[BaseException],
        __traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        """Stop the AMQPSystem.

        Args:
            __exc_type: AbstractAsyncContextManager argument.
            __exc_value: AbstractAsyncContextManager argument.
            __traceback: AbstractAsyncContextManager argument.

        Returns: None.
        """
        await self.stop()
        return await super().__aexit__(__exc_type, __exc_value, __traceback)

    def run_forever(self) -> None:
        """Start the AMQPSystem and run it forever.

        Returns:
            None
        """
        loop = asyncio.get_event_loop()
        # Setup everything
        loop.run_until_complete(self.start())
        # Run forever listening to messages
        loop.run_forever()
        # Clean up everything
        loop.run_until_complete(self.stop())
        loop.close()

    async def _on_message(
        self, callback: CallbackType, message: IncomingMessage
    ) -> None:
        """Message handler.

        Handles logging, metrics, retrying and exception handling.

        Args:
            callback: The callback to call with the message.
            message: The message to deliver to the callback.

        Returns:
            None
        """
        assert message.routing_key is not None
        routing_key = message.routing_key
        function_name = function_to_name(callback)
        log = logger.bind(function=function_name, routing_key=routing_key)

        log.debug("Received message")
        try:
            with _handle_receive_metrics(routing_key, function_name):
                # Requeue messages on exceptions, so they can be retried.
                async with message.process(requeue=True):
                    await callback(message=message, context=self.context)
        except Exception as exception:
            log.exception("Exception during on_message()")
            raise exception

    async def _publish_message(self, routing_key: str, payload: dict) -> None:
        """Publish a message to the given routing key.

        Args:
            routing_key: The routing key to send the message to.
            payload: The message payload.

        Returns:
            None
        """
        if self._exchange is None:
            raise ValueError("Must call start() before publish message!")

        with _handle_publish_metrics(routing_key):
            message = Message(body=json.dumps(payload).encode("utf-8"))
            await self._exchange.publish(routing_key=routing_key, message=message)
