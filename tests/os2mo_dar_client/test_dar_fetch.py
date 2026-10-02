# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from uuid import UUID

import pytest
from aiohttp import ClientResponseError

from fastramqpi.os2mo_dar_client import AsyncDARClient
from tests.os2mo_dar_client.conftest import assert_dar_response
from tests.os2mo_dar_client.conftest import dar_lookup
from tests.os2mo_dar_client.conftest import dar_non_existent
from tests.os2mo_dar_client.conftest import dar_parameterize
from tests.os2mo_dar_client.conftest import invalid_token

pytestmark = pytest.mark.integration_test


@pytest.mark.parametrize(*dar_parameterize)
async def test_dar_fetch_single(
    adarclient: AsyncDARClient, uuid: UUID, expected: dict[str, str]
) -> None:
    """Test lookup of single entry passes."""
    async with adarclient:
        result = await adarclient.fetch_single(uuid)
    assert_dar_response(result, expected)


@pytest.mark.parametrize("uuid", dar_non_existent)
async def test_dar_fetch_single_non_existent(
    adarclient: AsyncDARClient, uuid: UUID
) -> None:
    """Test lookup of a single non-existent entry fails."""
    async with adarclient:
        with pytest.raises(ValueError) as excinfo:
            await adarclient.fetch_single(uuid)
    assert "No address match found in DAR" in str(excinfo.value)


@pytest.mark.parametrize(*dar_parameterize)
async def test_dar_fetch(
    adarclient: AsyncDARClient, uuid: UUID, expected: dict[str, str]
) -> None:
    """Test lookup of single entry using dar_fetch passes."""
    async with adarclient:
        results, missing = await adarclient.fetch({uuid})
    assert not missing
    assert len(results) == 1
    result = next(iter(results.values()))
    assert_dar_response(result, expected)


@pytest.mark.parametrize("uuid", dar_non_existent)
async def test_dar_fetch_non_existent(adarclient: AsyncDARClient, uuid: UUID) -> None:
    """Test lookup of single non-existent entry using dar_fetch fails."""
    async with adarclient:
        results, missing = await adarclient.fetch({uuid})
    assert len(missing) == 1
    assert not results
    result = next(iter(missing))
    assert result == uuid


async def test_dar_fetch_zero(adarclient: AsyncDARClient) -> None:
    """Test lookup of zero entries using dar_fetch passes."""
    async with adarclient:
        results, missing = await adarclient.fetch(set())
    assert len(missing) == 0
    assert len(results) == 0


async def test_dar_fetch_multiple(adarclient: AsyncDARClient) -> None:
    """Test lookup of multiple entries using dar_fetch passes."""
    async with adarclient:
        results, missing = await adarclient.fetch(set(dar_lookup.keys()))
    assert not missing
    assert len(results) == len(dar_lookup)
    for uuid, expected in dar_lookup.items():
        result = results[uuid]
        assert_dar_response(result, expected)


async def test_dar_fetch_multiple_chunked(adarclient: AsyncDARClient) -> None:
    """Test lookup of multiple entries using dar_fetch passes."""
    async with adarclient:
        results, missing = await adarclient.fetch(set(dar_lookup.keys()), chunk_size=1)
    assert not missing
    assert len(results) == len(dar_lookup)
    for uuid, expected in dar_lookup.items():
        result = results[uuid]
        assert_dar_response(result, expected)


async def test_dar_fetch_multiple_non_existent(adarclient: AsyncDARClient) -> None:
    """Test lookup of multiple non-existent entries using dar_fetch fails."""
    async with adarclient:
        results, missing = await adarclient.fetch(dar_non_existent)
    assert len(missing) == len(dar_non_existent)
    assert not results
    for uuid in dar_non_existent:
        assert uuid in missing


async def test_dar_fetch_multiple_mixed_existence(adarclient: AsyncDARClient) -> None:
    """Test lookup of multiple mixed-existent entries using dar_fetch."""
    async with adarclient:
        results, missing = await adarclient.fetch(
            set.union(dar_non_existent, set(dar_lookup.keys()))
        )
    assert len(missing) == len(dar_non_existent)
    assert len(results) == len(dar_lookup)
    for uuid in dar_non_existent:
        assert uuid in missing
    for uuid, expected in dar_lookup.items():
        result = results[uuid]
        assert_dar_response(result, expected)


async def test_dar_fetch_single_clientresponse_error() -> None:
    """Test that non-404 ClientResponseErrors are propagated."""
    uuid = next(iter(dar_lookup))
    async with AsyncDARClient(token=invalid_token) as adarclient:
        with pytest.raises(ClientResponseError) as excinfo:
            await adarclient.fetch_single(uuid)
    assert excinfo.value.status == 400


async def test_dar_fetch_clientresponse_error() -> None:
    """Test that non-404 ClientResponseErrors are propagated."""
    async with AsyncDARClient(token=invalid_token) as adarclient:
        with pytest.raises(ClientResponseError) as excinfo:
            await adarclient.fetch(set(dar_lookup.keys()))
    assert excinfo.value.status == 400
