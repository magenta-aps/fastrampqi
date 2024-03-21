# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import patch

import pytest

from fastramqpi.ra_utils.sentry_init import sentry_init
from fastramqpi.ra_utils.sentry_init import Settings

env_dsn = "http://test.sentry.nope/env"
init_dsn = "http://test.sentry.nope/init"


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", env_dsn)
    monkeypatch.setenv("SENTRY_RELEASE", "TEST")


def test_settings():
    assert Settings(dsn=init_dsn)


def test_env_settings(mock_env):
    assert Settings(dsn=env_dsn)


@patch("sentry_sdk.init")
def test_sentry_init(mock_sentry):
    sentry_init(dsn=init_dsn, release="test")
    mock_sentry.assert_called_once_with(
        dsn=init_dsn,
        release="test",
        environment=None,
        server_name=None,
        traces_sample_rate=None,
        max_breadcrumbs=None,
        debug=None,
        attach_stacktrace=None,
        integrations=None,
    )


@patch("sentry_sdk.init")
def test_sentry_init_empty(mock_sentry):
    sentry_init()
    mock_sentry.assert_not_called()


@patch("sentry_sdk.init")
def test_sentry_init_env(mock_sentry, mock_env):
    sentry_init()
    mock_sentry.assert_called_once_with(
        dsn=env_dsn,
        release="TEST",
        environment=None,
        server_name=None,
        traces_sample_rate=None,
        max_breadcrumbs=None,
        debug=None,
        attach_stacktrace=None,
        integrations=None,
    )
