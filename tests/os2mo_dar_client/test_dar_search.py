# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from uuid import UUID

import aiohttp
import pytest

from fastramqpi.os2mo_dar_client import AsyncDARClient
from fastramqpi.os2mo_dar_client import DARClient
from tests.os2mo_dar_client.conftest import invalid_token


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "address,expected",
    [
        # Three results: the address itself, and its "st." and "1." floors
        (
            "Silkeborgvej 260, 8230 Åbyhøj",
            UUID("5bc8d53a-ac6f-4d57-ad53-10063f38cc17"),
        ),
        # Single result
        (
            "Silkeborgvej 260, st., 8230 Åbyhøj",
            UUID("6823f3c3-636b-4568-875e-f94786807cc5"),
        ),
        # Nine results: the "1." floor and its apartments
        (
            "Silkeborgvej 2, 1., 8000 Aarhus C",
            UUID("f6eb9610-3dab-48ce-9ae2-5a34aae1a914"),
        ),
    ],
)
async def test_search_match(
    adarclient: AsyncDARClient, address: str, expected: UUID
) -> None:
    async with adarclient:
        result = await adarclient.search(address)
    assert result == expected


@pytest.mark.integration_test
def test_search_match_sync(darclient: DARClient) -> None:
    with darclient:
        result = darclient.search("Silkeborgvej 260, 8230 Åbyhøj")
    assert result == UUID("5bc8d53a-ac6f-4d57-ad53-10063f38cc17")


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "address",
    [
        # Partial match, multiple results but no exact title match
        "Silkeborgvej 260",
        # No results at all
        "Flyvervej x, Svendborg",
    ],
)
async def test_search_no_match(adarclient: AsyncDARClient, address: str) -> None:
    async with adarclient:
        result = await adarclient.search(address)
    assert result is None


@pytest.mark.integration_test
async def test_search_error() -> None:
    async with AsyncDARClient(token=invalid_token) as adarclient:
        with pytest.raises(aiohttp.ClientResponseError):
            await adarclient.search("Silkeborgvej 260, 8230 Åbyhøj")
