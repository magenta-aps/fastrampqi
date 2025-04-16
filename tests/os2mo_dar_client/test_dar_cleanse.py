# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from functools import partial
from unittest.mock import MagicMock

import pytest
from aiohttp import ClientResponseError

from fastramqpi.os2mo_dar_client import AddressType
from fastramqpi.os2mo_dar_client import AsyncDARClient

from .utils import assert_dar_response
from .utils import dar_cleanse_parameterize
from .utils import dar_cleanse_unspecific_match


@pytest.mark.parametrize(*dar_cleanse_parameterize)
async def test_cleanse_single(
    adarclient: AsyncDARClient, address_string: str, expected: dict[str, str]
) -> None:
    """Test cleansing of single address string passes."""
    async with adarclient:
        result = await adarclient.cleanse_single(address_string)

    assert_dar_response(result, expected)


async def test_cleanse_invalid_addrtype(adarclient: AsyncDARClient) -> None:
    async with adarclient:
        with pytest.raises(ValueError) as excinfo:
            await adarclient.cleanse_single("", [AddressType.HISTORIC_ADDRESS])
        assert "DAR does not support historic cleansing" in str(excinfo.value)


@pytest.mark.parametrize("address_string", dar_cleanse_unspecific_match)
async def test_cleanse_single_unspecific(
    adarclient: AsyncDARClient, address_string: str
) -> None:
    """Test lookup of a single non-existent entry fails."""
    async with adarclient:
        with pytest.raises(ValueError) as excinfo:
            await adarclient.cleanse_single(address_string)
        assert "No address match found from cleansing in DAR" in str(excinfo.value)


async def test_cleanse_single_clientresponse_error(adarclient: AsyncDARClient) -> None:
    """Test that ClientResponseErrors are propagated."""

    SeededClientResponseError = partial(
        ClientResponseError,
        history=None,  # type: ignore
        request_info=None,  # type: ignore
    )
    address_string = next(iter(dar_cleanse_unspecific_match))

    # 404 are retried as next type
    with pytest.raises(ValueError) as excinfo1:
        async with adarclient:
            adarclient._get_session().get = MagicMock(  # type: ignore
                side_effect=SeededClientResponseError(status=404)
            )
            await adarclient.cleanse_single(address_string)
        assert "No address match found in DAR" in str(excinfo1.value)

    # All others are propagated as-is
    with pytest.raises(ClientResponseError) as excinfo2:
        async with adarclient:
            adarclient._get_session().get = MagicMock(  # type: ignore
                side_effect=SeededClientResponseError()
            )
            await adarclient.cleanse_single(address_string)
        assert "BOOM" in str(excinfo2.value)
