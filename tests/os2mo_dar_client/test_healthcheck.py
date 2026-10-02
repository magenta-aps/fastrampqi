# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from warnings import catch_warnings

import pytest
from more_itertools import first

from fastramqpi.os2mo_dar_client import AsyncDARClient
from fastramqpi.os2mo_dar_client import DARClient
from tests.os2mo_dar_client.conftest import invalid_token


@pytest.mark.integration_test
def test_healthcheck_sync(darclient: DARClient) -> None:
    result = False

    assert darclient._session is None
    with pytest.raises(ValueError) as excinfo:
        darclient.healthcheck()  # type: ignore
    assert "Session not set" in str(excinfo)

    assert darclient._session is None
    with darclient:
        assert darclient._session is not None
        result = darclient.healthcheck()
    assert result is True
    assert darclient._session is None

    assert darclient._session is None
    darclient.aopen()  # type: ignore
    assert darclient._session is not None
    result = darclient.healthcheck()
    darclient.aclose()  # type: ignore
    assert result is True
    assert darclient._session is None


@pytest.mark.integration_test
async def test_healthcheck_async(darclient: DARClient) -> None:
    result = False

    assert darclient._session is None
    with pytest.raises(ValueError) as excinfo:
        await darclient.healthcheck()
    assert "Session not set" in str(excinfo)

    assert darclient._session is None
    async with darclient:
        assert darclient._session is not None
        result = await darclient.healthcheck()
    assert result is True
    assert darclient._session is None

    assert darclient._session is None
    await darclient.aopen()
    assert darclient._session is not None
    result = await darclient.healthcheck()
    await darclient.aclose()
    assert result is True
    assert darclient._session is None


async def test_multiple_call_warnings() -> None:
    darclient = DARClient()
    with catch_warnings(record=True) as warnings:
        await darclient.aopen()
        await darclient.aclose()
        assert len(warnings) == 0

    with catch_warnings(record=True) as warnings:
        await darclient.aopen()
        assert len(warnings) == 0
    with catch_warnings(record=True) as warnings:
        await darclient.aopen()  # This triggers a warning
        assert len(warnings) == 1
        warning = first(warnings)
        assert issubclass(warning.category, UserWarning)
        assert "aopen called with existing session" in str(warning.message)
    with catch_warnings(record=True) as warnings:
        await darclient.aclose()
        assert len(warnings) == 0

    with catch_warnings(record=True) as warnings:
        await darclient.aclose()  # This triggers a warning
        assert len(warnings) == 1
        warning = first(warnings)
        assert issubclass(warning.category, UserWarning)
        assert "aclose called without session" in str(warning.message)


@pytest.mark.integration_test
async def test_healthcheck_non_200() -> None:
    """Test that a non-200 reply (here a 400 due to an invalid token) fails."""
    async with AsyncDARClient(token=invalid_token) as darclient:
        result = await darclient.healthcheck()
    assert result is False


@pytest.mark.integration_test
async def test_healthcheck_timeout() -> None:
    """Test that a timeout fails."""
    async with AsyncDARClient() as darclient:
        # No reply from Adressevælgeren arrives within a millisecond
        result = await darclient.healthcheck(0.001)  # type: ignore[arg-type]
    assert result is False


@pytest.mark.integration_test
async def test_healthcheck_client_error() -> None:
    """Test that a connection error fails."""
    darclient = AsyncDARClient()
    # The .invalid top-level domain is guaranteed to never resolve (RFC 6761)
    darclient._baseurl = "https://adressevaelger.invalid"
    async with darclient:
        result = await darclient.healthcheck()
    assert result is False
