# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any
from uuid import UUID

import pytest
from tenacity import stop_after_delay

from fastramqpi.os2mo_dar_client import AsyncDARClient
from fastramqpi.os2mo_dar_client import DARClient

# Actual DAR UUIDS with actual response snippets from Adressevælgeren
# Note: These tests will fail if they go out of sync with Adressevælgeren
dar_lookup: dict[UUID, dict[str, Any]] = {
    UUID("0a3f50c4-379f-32b8-e044-0003ba298018"): {
        "id": "0a3f50c4-379f-32b8-e044-0003ba298018",
        "vejnavn": "Skt. Johannes Allé",
        "husnr": "2",
        "postnr": "8000",
        "postnrnavn": "Aarhus C",
        "kommunekode": "0751",
        "betegnelse": "Skt. Johannes Allé 2, 8000 Aarhus C",
        "adgangsadresseid": "0a3f5096-e43f-32b8-e044-0003ba298018",
        "x": 0.0,
        "y": 0.0,
    },
    UUID("03c59320-1edd-40f4-9bbe-af135475205e"): {
        "id": "03c59320-1edd-40f4-9bbe-af135475205e",
        "vejnavn": "Julsøvej",
        "husnr": "14",
        "postnr": "8680",
        "postnrnavn": "Ry",
        "kommunekode": "0746",
        "vejkode": "0499",
    },
    # Access address
    UUID("0a3f5095-12d6-32b8-e044-0003ba298018"): {
        "id": "0a3f5095-12d6-32b8-e044-0003ba298018",
        "vejnavn": "Julsøvej",
        "husnr": "14",
        "postnr": "8680",
        "postnrnavn": "Ry",
        "kommunekode": "0746",
        "betegnelse": "Julsøvej 14, 8680 Ry",
    },
}

dar_parameterize = ("uuid,expected", list(dar_lookup.items()))

dar_non_existent = {
    UUID("00000000-0000-0000-0000-000000000000"),
    UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
}

# Actual DAR cleanse results
dar_cleanse_parameterize = (
    "address_string,expected",
    [
        (
            "Sankt Johannes Alle 2, 8000 Aarhus C",
            {
                "id": "0a3f50c4-379f-32b8-e044-0003ba298018",
                "vejnavn": "Skt. Johannes Allé",
                "husnr": "2",
                "postnr": "8000",
                "postnrnavn": "Aarhus C",
            },
        ),
        (
            "Rådhuspladsen 1, 8000 Aarhus C",
            {
                "id": "0a3f50c4-05a3-32b8-e044-0003ba298018",
                "vejnavn": "Rådhuspladsen",
                "husnr": "1",
                "postnr": "8000",
                "postnrnavn": "Aarhus C",
            },
        ),
    ],
)
dar_cleanse_unspecific_match = {"Flyvervej x, Svendborg", ""}

# Adressevælgeren rejects tokens shorter than 10 characters with a 400
invalid_token = "invalid"


def assert_dar_response(result: dict, expected: dict) -> None:
    for key in expected.keys():
        assert result[key] == expected[key]


@pytest.fixture(autouse=True)
def no_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable retrying, so failing requests do not take 30 seconds."""
    for method in [AsyncDARClient._fetch_single, AsyncDARClient._fetch_non_chunked]:
        monkeypatch.setattr(method.retry, "stop", stop_after_delay(0))  # type: ignore


@pytest.fixture
async def adarclient() -> AsyncDARClient:
    return AsyncDARClient()


@pytest.fixture
async def darclient() -> DARClient:
    # Must be constructed within the event loop, as `Syncable` binds to it
    return DARClient()
