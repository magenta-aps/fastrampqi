# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
# pylint: disable=unused-argument
"""Test our settings handling."""
import pytest
from pydantic.v1 import ValidationError

from fastramqpi.config import Settings


def test_missing_client_secret() -> None:
    """Test that we must add client_secret to construct settings."""
    with pytest.raises(ValidationError) as excinfo:
        Settings()
    assert "client_secret\n  field required" in str(excinfo.value)


def test_graphql_timeout_default(settings: Settings) -> None:
    """Test that default GraphQL client timeout is set correctly"""
    assert settings.graphql_timeout == 120
