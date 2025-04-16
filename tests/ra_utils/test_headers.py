# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import time
from datetime import timedelta
from logging import getLogger
from typing import Any

import pytest
import requests
from hypothesis import example
from hypothesis import given
from hypothesis import strategies as st
from pytest import MonkeyPatch
from pytest_mock import MockerFixture

from fastramqpi.ra_utils.headers import AuthError
from fastramqpi.ra_utils.headers import TokenSettings


class MockFetchKeycloakToken:
    def __init__(self, expires: int) -> None:
        self.expires = expires

    def __call__(self, *args: Any, **kwargs: Any) -> tuple:
        return self.expires, "dummy token"

    def cache_clear(self) -> None:
        pass


class MockResponse:
    def __init__(self, response_dict: dict, raise_msg: str = "") -> None:
        self.response = response_dict
        self.raise_msg = raise_msg

    def json(self) -> dict:
        return self.response

    def raise_for_status(self) -> None:
        if self.raise_msg:
            raise requests.RequestException(self.raise_msg)


def test_init(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("SAML_TOKEN", "test token")
    with pytest.deprecated_call():
        assert TokenSettings()
    monkeypatch.delenv("SAML_TOKEN", raising=False)
    monkeypatch.setenv("CLIENT_SECRET", "test secret")
    assert TokenSettings()


def test_validation(monkeypatch: MonkeyPatch) -> None:
    # delete token/secret if they exist
    monkeypatch.delenv("SAML_TOKEN", raising=False)
    monkeypatch.delenv("CLIENT_SECRET", raising=False)
    with pytest.warns(UserWarning, match="No secret or token given"):
        TokenSettings()


@given(t_delta=st.timedeltas())
def test_fetch_keycloak(t_delta: timedelta) -> None:
    def mock_post(*args: Any, **kwargs: Any) -> MockResponse:
        return MockResponse(
            {"expires_in": t_delta.total_seconds(), "access_token": "test_token"}
        )

    with MonkeyPatch.context() as m:
        m.setenv("CLIENT_SECRET", "test secret")
        m.setattr(requests, "post", mock_post)
        settings = TokenSettings()
        settings._fetch_keycloak_token()


@pytest.mark.filterwarnings("ignore: No secret or token given")
def test_fetch_keycloak_errors(monkeypatch: MonkeyPatch) -> None:
    fail_msg = "Oh no"

    def mock_post(*args: Any, **kwargs: Any) -> MockResponse:
        return MockResponse(
            {"expires_in": time.time(), "access_token": "test_token"},
            raise_msg=fail_msg,
        )

    monkeypatch.delenv("CLIENT_SECRET", raising=False)
    monkeypatch.setattr(requests, "post", mock_post)
    settings = TokenSettings()
    with pytest.raises(AuthError, match="No client secret given"):
        settings._fetch_keycloak_token()

    # Set a client secret
    monkeypatch.setenv("CLIENT_SECRET", "test secret")
    settings = TokenSettings()
    settings._fetch_keycloak_token.cache_clear()
    with pytest.raises(AuthError, match=f"Failed to get Keycloak token: {fail_msg}"):
        settings._fetch_keycloak_token()


@given(t_delta=st.timedeltas())
@example(t_delta=timedelta(seconds=-1))
def test_fetch_bearer(t_delta: timedelta) -> None:
    def mock_post(*args: Any, **kwargs: Any) -> MockResponse:
        return MockResponse(
            {"expires_in": t_delta.total_seconds(), "access_token": "test_token"}
        )

    with MonkeyPatch.context() as m:
        m.setenv("CLIENT_SECRET", "test secret")
        m.setattr(requests, "post", mock_post)
        settings = TokenSettings()
        assert settings._fetch_bearer()


@pytest.mark.filterwarnings("ignore: Using SAML tokens")
def test_get_headers(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        TokenSettings, "_fetch_bearer", lambda self, force, logger: "Bearer token"
    )
    monkeypatch.setenv("CLIENT_SECRET", "test secret")
    settings = TokenSettings()
    headers = settings.get_headers()
    assert "Authorization" in headers
    assert "Bearer token" in headers.values()
    monkeypatch.setenv("SAML_TOKEN", "test token")
    settings = TokenSettings()
    headers = settings.get_headers()
    assert "Session" in headers
    assert "test token" in headers.values()


def test_logger_called(monkeypatch: MonkeyPatch, mocker: MockerFixture) -> None:
    monkeypatch.setenv("CLIENT_SECRET", "test secret")
    monkeypatch.setattr(
        TokenSettings, "_fetch_keycloak_token", MockFetchKeycloakToken(-1)
    )
    logger = getLogger("mock_logger")
    spy = mocker.spy(logger, "debug")

    settings = TokenSettings()
    settings._fetch_bearer(logger=logger)

    spy.assert_called_once_with("New token fetched", expires=-1, token="dummy token")


# Test token renewal mechanism with respect to token expiration


def _setup_token_lifespan_test(
    monkeypatch: MonkeyPatch,
    mocker: MockerFixture,
    monotonic_time: Any,
    spy_function: Any,
) -> None:
    monkeypatch.setattr(
        TokenSettings, "_fetch_keycloak_token", MockFetchKeycloakToken(400)
    )
    monkeypatch.setattr("time.monotonic", lambda: monotonic_time)

    logger = getLogger("mock_logger")
    spy = mocker.spy(logger, "debug")

    settings = TokenSettings()
    settings._fetch_bearer(logger=logger)

    spy_method = getattr(spy, spy_function)
    spy_method()


def test_renew_token_when_actual_expiration_time_passed(
    monkeypatch: MonkeyPatch, mocker: MockerFixture
) -> None:
    _setup_token_lifespan_test(monkeypatch, mocker, 500.0, "assert_called_once")


def test_renew_token_when_offset_expiration_time_passed(
    monkeypatch: MonkeyPatch, mocker: MockerFixture
) -> None:
    _setup_token_lifespan_test(monkeypatch, mocker, 380.0, "assert_called_once")


def test_do_not_renew_token_when_offset_expiration_time_not_passed(
    monkeypatch: MonkeyPatch, mocker: MockerFixture
) -> None:
    _setup_token_lifespan_test(monkeypatch, mocker, 360.0, "assert_not_called")


def test_force_token_renewal(monkeypatch: MonkeyPatch, mocker: MockerFixture) -> None:
    monkeypatch.setenv("CLIENT_SECRET", "test secret")
    monkeypatch.setattr(
        TokenSettings, "_fetch_keycloak_token", MockFetchKeycloakToken(-1)
    )

    logger = getLogger("mock_logger")
    spy = mocker.spy(logger, "debug")

    settings = TokenSettings()
    settings._fetch_bearer(force=True, logger=logger)

    spy.assert_called_once()
