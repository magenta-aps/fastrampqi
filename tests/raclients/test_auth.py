# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import AsyncGenerator
from typing import Generator
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as
from respx import MockRouter

from fastramqpi.raclients.auth import AuthenticatedAsyncHTTPXClient
from fastramqpi.raclients.auth import AuthenticatedHTTPXClient
from fastramqpi.raclients.auth import BaseAuthenticatedClient
from fastramqpi.raclients.auth import keycloak_token_endpoint


@pytest.fixture
def base_client(oidc_client_params: dict) -> BaseAuthenticatedClient:
    return BaseAuthenticatedClient(session=None, **oidc_client_params)


@pytest.fixture
def client(oidc_client_params: dict) -> Generator[AuthenticatedHTTPXClient, None, None]:
    with AuthenticatedHTTPXClient(**oidc_client_params) as client:
        yield client


@pytest.fixture
async def async_client(
    oidc_client_params: dict,
) -> AsyncGenerator[AuthenticatedAsyncHTTPXClient, None]:
    async with AuthenticatedAsyncHTTPXClient(**oidc_client_params) as client:
        yield client


def test_authenticated_httpx_client_init(client: AuthenticatedHTTPXClient) -> None:
    assert client.client_id == "AzureDiamond"
    assert client.client_secret == "hunter2"
    assert client.token_endpoint == "https://oidc.example.org/oauth2/v2.0/token"
    assert client.token_endpoint_auth_method == "client_secret_post"
    assert client.metadata["token_endpoint"] == client.token_endpoint
    assert client.metadata["grant_type"] == "client_credentials"


def test_should_fetch_token_if_not_set(base_client: BaseAuthenticatedClient) -> None:
    base_client.token = None
    assert base_client.should_fetch_token("http://www.example.org") is True


def test_should_not_fetch_token_if_set(base_client: BaseAuthenticatedClient) -> None:
    base_client.token = True
    assert base_client.should_fetch_token("http://www.example.org") is False


def test_should_not_fetch_token_if_token_endpoint(
    base_client: BaseAuthenticatedClient,
) -> None:
    base_client.token = None
    assert base_client.should_fetch_token(str(base_client.token_endpoint)) is False


def test_should_not_fetch_token_if_withhold_token(
    base_client: BaseAuthenticatedClient,
) -> None:
    base_client.token = None
    assert (
        base_client.should_fetch_token("http://www.example.org", withhold_token=True)
        is False
    )


def test_should_not_fetch_token_if_no_auth(
    base_client: BaseAuthenticatedClient,
) -> None:
    base_client.token = None
    assert base_client.should_fetch_token("http://www.example.org", auth=None) is False


def test_authenticated_httpx_client_decorates_request(
    client: AuthenticatedHTTPXClient,
) -> None:
    with patch(
        "authlib.integrations.httpx_client.oauth2_client.OAuth2Client.request"
    ) as request_mock:
        client.request(
            method="1",
            url="2",
            withhold_token=True,
            auth=("4", "5"),
            some_kwarg=5,
        )
        request_mock.assert_called_once_with("1", "2", True, ("4", "5"), some_kwarg=5)


@pytest.mark.asyncio
async def test_async_authenticated_httpx_client_decorates_request(
    async_client: AuthenticatedAsyncHTTPXClient,
) -> None:
    with patch(
        "authlib.integrations.httpx_client.oauth2_client.AsyncOAuth2Client.request"
    ) as request_mock:
        await async_client.request(
            method="1",
            url="2",
            withhold_token=True,
            auth=("4", "5"),
            some_kwarg=5,
        )
        request_mock.assert_called_once_with("1", "2", True, ("4", "5"), some_kwarg=5)


def test_authenticated_httpx_client_fetches_token(
    client: AuthenticatedHTTPXClient,
) -> None:
    def set_token() -> None:
        client.token = True

    client.fetch_token = Mock(side_effect=set_token)
    with patch(
        "authlib.integrations.httpx_client.oauth2_client.OAuth2Client.request"
    ) as request_mock:
        client.get("http://www.example.org")
        client.get("http://www.example.net")  # test that it only fetches a token once

    client.fetch_token.assert_called_once()
    assert request_mock.call_count == 2


@pytest.mark.asyncio
async def test_async_authenticated_httpx_client_fetches_token(
    async_client: AuthenticatedAsyncHTTPXClient,
) -> None:
    def set_token() -> None:
        async_client.token = True

    async_client.fetch_token = AsyncMock(side_effect=set_token)
    with patch(
        "authlib.integrations.httpx_client.oauth2_client.AsyncOAuth2Client.request"
    ) as request_mock:
        await async_client.get("http://www.example.org")  # test that it only fetches a
        await async_client.get("http://www.example.net")  # token once

    async_client.fetch_token.assert_awaited_once()
    assert request_mock.call_count == 2


def test_integration_sends_token_in_request(
    client: AuthenticatedHTTPXClient,
    respx_mock: MockRouter,
    oidc_token_mock: str,
) -> None:
    respx_mock.get(
        "http://www.example.org",
        headers={
            "Authorization": f"Bearer {oidc_token_mock}",
        },
    )

    response = client.get("http://www.example.org")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_integration_async_sends_token_in_request(
    async_client: AuthenticatedAsyncHTTPXClient,
    respx_mock: MockRouter,
    oidc_token_mock: str,
) -> None:
    respx_mock.get(
        "http://www.example.org",
        headers={
            "Authorization": f"Bearer {oidc_token_mock}",
        },
    )

    response = await async_client.get("http://www.example.org")
    assert response.status_code == 200


def test_keycloak_token_endpoint() -> None:
    token_endpoint = keycloak_token_endpoint(
        auth_server=parse_obj_as(AnyHttpUrl, "https://keycloak.example.org/auth"),
        auth_realm="mordor",
    )
    assert (
        token_endpoint
        == "https://keycloak.example.org/auth/realms/mordor/protocol/openid-connect/token"
    )
