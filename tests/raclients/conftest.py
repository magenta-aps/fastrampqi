# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Callable
from typing import cast

import httpx
import pytest
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as
from respx import MockRouter

from raclients.auth import keycloak_token_endpoint

pytestmark = pytest.mark.respx(assert_all_called=True)


@pytest.fixture
def client_params() -> dict:
    return dict(
        client_id="AzureDiamond",
        client_secret="hunter2",
        auth_server=parse_obj_as(AnyHttpUrl, "https://keycloak.example.org/auth"),
        auth_realm="mordor",
    )


@pytest.fixture
def oidc_client_params() -> dict:
    return dict(
        client_id="AzureDiamond",
        client_secret="hunter2",
        token_endpoint="https://oidc.example.org/oauth2/v2.0/token",
    )


@pytest.fixture
def token_mocker(respx_mock: MockRouter) -> Callable[[AnyHttpUrl], str]:
    def mocker(token_endpoint: AnyHttpUrl) -> str:
        token = "my_token"
        respx_mock.post(url=str(token_endpoint)).mock(
            return_value=httpx.Response(
                200,
                json={
                    "token_type": "Bearer",
                    "access_token": token,
                },
            )
        )

        return token

    return mocker


@pytest.fixture
def token_mock(client_params: dict, token_mocker: Callable[[AnyHttpUrl], str]) -> str:
    return token_mocker(
        keycloak_token_endpoint(
            auth_server=client_params["auth_server"],
            auth_realm=client_params["auth_realm"],
        )
    )


@pytest.fixture
def oidc_token_mock(
    oidc_client_params: dict, token_mocker: Callable[[str], str]
) -> str:
    return token_mocker(oidc_client_params["token_endpoint"])
