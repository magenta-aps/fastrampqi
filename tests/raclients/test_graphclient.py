# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any

import httpx
import pytest
from gql import gql
from graphql import DocumentNode
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as
from respx import MockRouter

from fastramqpi.raclients.graph.client import GraphQLClient
from fastramqpi.raclients.graph.client import PersistentGraphQLClient

url = parse_obj_as(AnyHttpUrl, "https://os2mo.example.org/gql")


@pytest.fixture
def query() -> Any:
    return gql(
        """
        query MOQuery {
            users {
                id
            }
        }
        """
    )


@pytest.fixture
def query_mock(token_mock: str, respx_mock: MockRouter) -> dict:
    data = {"a": 1}
    respx_mock.post(
        url=url,
        json={"query": "query MOQuery {\n  users {\n    id\n  }\n}"},
        headers={"Authorization": f"Bearer {token_mock}"},
    ).mock(
        return_value=httpx.Response(200, json={"data": data}),
    )

    return data


def test_init_client(client_params: dict) -> None:
    httpx_client_kwargs = dict(timeout=123)
    with GraphQLClient(
        url=url, sync=True, **client_params, httpx_client_kwargs=httpx_client_kwargs
    ) as session:
        assert session.transport.client_args == dict(
            client_id="AzureDiamond",
            client_secret="hunter2",
            token_endpoint="https://keycloak.example.org/auth/realms/mordor/protocol/openid-connect/token",
            **httpx_client_kwargs,
        )


@pytest.mark.asyncio
async def test_init_async_client(client_params: dict) -> None:
    httpx_client_kwargs = dict(timeout=123)
    async with GraphQLClient(
        url=url, **client_params, httpx_client_kwargs=httpx_client_kwargs
    ) as session:
        assert session.transport.client_args == dict(
            client_id="AzureDiamond",
            client_secret="hunter2",
            token_endpoint="https://keycloak.example.org/auth/realms/mordor/protocol/openid-connect/token",
            **httpx_client_kwargs,
        )


def test_integration_client(
    client_params: dict, token_mock: str, query: DocumentNode, query_mock: dict
) -> None:
    with GraphQLClient(url=url, sync=True, **client_params) as session:
        result = session.execute(query)
        assert result == query_mock


@pytest.mark.asyncio
async def test_integration_async_client(
    client_params: dict, token_mock: str, query: DocumentNode, query_mock: dict
) -> None:
    async with GraphQLClient(url=url, **client_params) as session:
        result = await session.execute(query)
        assert result == query_mock


def test_integration_persistent_client(
    client_params: dict, token_mock: str, query: DocumentNode, query_mock: dict
) -> None:
    persistent_client = PersistentGraphQLClient(url=url, **client_params, sync=True)
    result_1 = persistent_client.execute(query)
    result_2 = persistent_client.execute(query)
    assert result_1 == result_2 == query_mock
    persistent_client.close()
    assert persistent_client.transport.client is None


@pytest.mark.asyncio
async def test_integration_async_persistent_client(
    client_params: dict, token_mock: str, query: DocumentNode, query_mock: dict
) -> None:
    persistent_client = PersistentGraphQLClient(url=url, **client_params)
    result_1 = await persistent_client.execute(query)
    result_2 = await persistent_client.execute(query)
    assert result_1 == result_2 == query_mock
    await persistent_client.aclose()
    assert persistent_client.transport.client is None
