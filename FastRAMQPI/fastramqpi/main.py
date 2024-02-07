# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
"""FastAPI + RAMQP Framework."""
from contextlib import asynccontextmanager
from functools import partial
from typing import Any
from typing import AsyncContextManager
from typing import AsyncGenerator
from typing import cast
from typing import Protocol
from typing import Type

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from raclients.graph.client import GraphQLClient as LegacyGraphQLClient
from raclients.modelclient.mo import ModelClient as LegacyModelClient
from ramqp.mo import MOAMQPSystem

from .config import ClientSettings
from .config import Settings
from .context import Context
from .fastapi import FastAPIIntegrationSystem


def construct_legacy_clients(
    graphql_version: int,
    settings: ClientSettings,
) -> tuple[LegacyGraphQLClient, LegacyModelClient]:
    """Construct legacy clients froms settings.

    Args:
        settings: Integration settings module.

    Returns:
        Tuple with PersistentGraphQLClient and ModelClient.
    """
    # DEPRECATED: ariadne-codegen is the preferred way to interface with GraphQL
    gql_client = LegacyGraphQLClient(
        url=f"{settings.mo_url}/graphql/v{graphql_version}",
        client_id=settings.client_id,
        client_secret=settings.client_secret.get_secret_value(),
        auth_realm=settings.auth_realm,
        auth_server=settings.auth_server,
        execute_timeout=settings.graphql_timeout,
        httpx_client_kwargs={"timeout": settings.graphql_timeout},
    )
    # DEPRECATED: GraphQL is the preferred way to interface with OS2mo
    model_client = LegacyModelClient(
        client_id=settings.client_id,
        client_secret=settings.client_secret.get_secret_value(),
        auth_realm=settings.auth_realm,
        auth_server=settings.auth_server,
        base_url=settings.mo_url,
    )
    return gql_client, model_client


class GraphQLClientProtocol(AsyncContextManager, Protocol):
    def __init__(
        self,
        url: str = "",
        headers: dict[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
        ws_url: Any = None,
        ws_headers: Any = None,
        ws_origin: Any = None,
        ws_connection_init_payload: Any = None,
    ) -> None:
        ...  # pragma: no cover


class FastRAMQPI(FastAPIIntegrationSystem):
    """FastRAMQPI (FastAPI + RAMQP) combined-system.

    Motivated by a lot a shared code between our AMQP integrations.
    """

    def __init__(
        self,
        application_name: str,
        settings: Settings,
        graphql_version: int,
        graphql_client_cls: Type[GraphQLClientProtocol] | None = None,
    ) -> None:
        super().__init__(application_name, settings)

        # Setup AMQPSystem
        amqp_settings = cast(Settings, self.settings).amqp
        amqp_settings.queue_prefix = amqp_settings.queue_prefix or application_name
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

        # Authenticated HTTPX Client
        mo_client = AsyncOAuth2Client(
            base_url=settings.mo_url,
            client_id=settings.client_id,
            client_secret=settings.client_secret.get_secret_value(),
            grant_type="client_credentials",
            # TODO: We should take a full token URL instead of hard-coding Keycloak's
            # URL scheme. Let's wait until the legacy clients are removed.
            token_endpoint=f"{settings.auth_server}/realms/{settings.auth_realm}/protocol/openid-connect/token",
            # TODO (https://github.com/lepture/authlib/issues/531): Hack to enable
            # automatic fetching of token on first call, instead of only refreshing.
            token={"expires_at": -1, "access_token": ""},
            timeout=settings.graphql_timeout,
        )

        @asynccontextmanager
        async def mo_client_manager(context: Context) -> AsyncGenerator[None, None]:
            async with mo_client as client:
                context["mo_client"] = client
                yield

        self.add_lifespan_manager(
            cast(AsyncContextManager, partial(mo_client_manager, self._context)())
        )

        # GraphQL Client
        if graphql_client_cls is not None:

            @asynccontextmanager
            async def graphql_client_manager(
                context: Context,
            ) -> AsyncGenerator[None, None]:
                graphql_client = graphql_client_cls(
                    url=f"{settings.mo_url}/graphql/v{graphql_version}",
                    http_client=mo_client,
                )
                async with graphql_client as client:
                    context["graphql_client"] = client
                    yield

            self.add_lifespan_manager(
                cast(
                    AsyncContextManager,
                    partial(graphql_client_manager, self._context)(),
                )
            )

        # Prepare legacy clients
        legacy_graphql_client, legacy_model_client = construct_legacy_clients(
            graphql_version=graphql_version,
            settings=cast(ClientSettings, self.settings),
        )
        # Expose legacy GraphQL connection (gql_client)
        self._context["legacy_graphql_client"] = legacy_graphql_client

        @asynccontextmanager
        async def legacy_graphql_session(
            context: Context,
        ) -> AsyncGenerator[None, None]:
            async with context["legacy_graphql_client"] as session:
                context["legacy_graphql_session"] = session
                yield

        self.add_lifespan_manager(
            cast(AsyncContextManager, partial(legacy_graphql_session, self._context)())
        )
        # Expose legacy Service API connection (model_client)
        self.add_lifespan_manager(legacy_model_client)
        self._context["legacy_model_client"] = legacy_model_client

    def get_amqpsystem(self) -> MOAMQPSystem:
        """Return the contained MOAMQPSystem.

        Returns:
            MOAQMPSystem.
        """
        return self.amqpsystem
