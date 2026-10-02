# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from aiohttp import ClientResponseError

from fastramqpi.os2mo_dar_client import AddressType
from fastramqpi.os2mo_dar_client import AsyncDARClient
from tests.os2mo_dar_client.conftest import assert_dar_response
from tests.os2mo_dar_client.conftest import dar_cleanse_parameterize
from tests.os2mo_dar_client.conftest import dar_cleanse_unspecific_match
from tests.os2mo_dar_client.conftest import invalid_token

pytestmark = pytest.mark.integration_test


@pytest.mark.parametrize(*dar_cleanse_parameterize)
async def test_cleanse_single(
    adarclient: AsyncDARClient, address_string: str, expected: dict[str, str]
) -> None:
    """Test cleansing of single address string passes."""
    async with adarclient:
        result = await adarclient.cleanse_single(address_string)

    assert_dar_response(result, expected)


@pytest.mark.parametrize("address_string", dar_cleanse_unspecific_match)
async def test_cleanse_single_unspecific(
    adarclient: AsyncDARClient, address_string: str
) -> None:
    """Test cleansing of an unspecific address string fails."""
    async with adarclient:
        with pytest.raises(ValueError) as excinfo:
            await adarclient.cleanse_single(address_string)
    assert "No address match found from cleansing in DAR" in str(excinfo.value)


async def test_cleanse_single_clientresponse_error() -> None:
    """Test that non-404 ClientResponseErrors are propagated."""
    async with AsyncDARClient(token=invalid_token) as adarclient:
        with pytest.raises(ClientResponseError) as excinfo:
            await adarclient.cleanse_single("Sankt Johannes Alle 2, 8000 Aarhus C")
    assert excinfo.value.status == 400


async def test_cleanse_single_access_address(adarclient: AsyncDARClient) -> None:
    """Test cleansing with ACCESS_ADDRESS returns the access address, not the address."""
    async with adarclient:
        result = await adarclient.cleanse_single(
            "Sankt Johannes Alle 2, 8000 Aarhus C", [AddressType.ACCESS_ADDRESS]
        )
    assert_dar_response(
        result,
        {
            "id": "0a3f5096-e43f-32b8-e044-0003ba298018",
            "vejnavn": "Skt. Johannes Allé",
            "husnr": "2",
            "postnr": "8000",
            "betegnelse": "Skt. Johannes Allé 2, 8000 Aarhus C",
        },
    )
    assert "adgangsadresseid" not in result
