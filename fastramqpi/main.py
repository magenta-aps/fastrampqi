# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
"""FastAPI + RAMQP Framework."""
from contextlib import asynccontextmanager
from functools import partial
from typing import AsyncContextManager
from typing import AsyncGenerator
from typing import cast

from raclients.graph.client import GraphQLClient
from raclients.modelclient.mo import ModelClient
from ramqp.mo import MOAMQPSystem

from .config import ClientSettings
from .config import Settings
from .context import Context
from .fastapi import FastAPIIntegrationSystem
from .healthcheck import healthcheck_gql
from .healthcheck import healthcheck_model_client


def construct_clients(
    settings: ClientSettings,
) -> tuple[GraphQLClient, ModelClient]:
    """Construct clients froms settings.

    Args:
        settings: Integration settings module.

    Returns:
        Tuple with PersistentGraphQLClient and ModelClient.
    """
    client_kwargs = dict(
        client_id=settings.client_id,
        client_secret=settings.client_secret.get_secret_value(),
        auth_realm=settings.auth_realm,
        auth_server=settings.auth_server,
    )

    gql_client = GraphQLClient(
        url=settings.mo_url + "/graphql",
        execute_timeout=settings.graphql_timeout,
        httpx_client_kwargs={"timeout": settings.graphql_timeout},
        **client_kwargs,
    )
    model_client = ModelClient(
        base_url=settings.mo_url,
        **client_kwargs,
    )
    return gql_client, model_client


class FastRAMQPI(FastAPIIntegrationSystem):
    """FastRAMQPI (FastAPI + RAMQP) combined-system.

    Motivated by a lot a shared code between our AMQP integrations.
    """

    def __init__(self, application_name: str, settings: Settings | None = None) -> None:
        if settings is None:
            settings = Settings()
        super().__init__(application_name, settings)

        # Setup AMQPSystem
        amqp_settings = cast(Settings, self.settings).amqp
        amqp_settings = amqp_settings.copy(
            update={"queue_prefix": self.get_context()["name"]}
        )
        self.amqpsystem = MOAMQPSystem(
            settings=amqp_settings, context=self.get_context()
        )
        # Let AMQPSystems lifespan follow ASGI lifespan
        self.add_lifespan_manager(self.amqpsystem)

        async def healthcheck_amqp(context: Context) -> bool:
            """AMQP Healthcheck wrapper.

            Args:
                context: unused context dict.

            Returns:
                Whether the AMQPSystem is OK.
            """
            amqpsystem = context["amqpsystem"]
            return cast(bool, amqpsystem.healthcheck())

        self.add_healthcheck(name="AMQP", healthcheck=healthcheck_amqp)
        self._context["amqpsystem"] = self.amqpsystem

        # Prepare clients
        graphql_client, model_client = construct_clients(
            cast(ClientSettings, self.settings)
        )
        # Check and expose GraphQL connection (gql_client)
        self.add_healthcheck("GraphQL", healthcheck_gql)
        self._context["graphql_client"] = graphql_client

        @asynccontextmanager
        async def graphql_session(context: Context) -> AsyncGenerator[None, None]:
            async with context["graphql_client"] as session:
                context["graphql_session"] = session
                yield

        self.add_lifespan_manager(
            cast(AsyncContextManager, partial(graphql_session, self._context)())
        )
        # Check and expose Service API connection (model_client)
        self.add_lifespan_manager(model_client)
        self.add_healthcheck("Service API", healthcheck_model_client)
        self._context["model_client"] = model_client

    def get_amqpsystem(self) -> MOAMQPSystem:
        """Return the contained MOAMQPSystem.

        Returns:
            MOAQMPSystem.
        """
        return self.amqpsystem
