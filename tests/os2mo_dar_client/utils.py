# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple
from uuid import UUID

import pytest
from aiohttp import ClientTimeout
from aiohttp import web
from aiohttp.test_utils import TestClient
from tenacity import stop_after_delay

from fastramqpi.os2mo_dar_client import AsyncDARClient
from fastramqpi.os2mo_dar_client import DARClient
from fastramqpi.os2mo_dar_client.dar_client import ALL_ADDRESS_TYPES
from fastramqpi.ra_utils.syncable import Syncable

# Actual DAR UUIDS with actual response snippets
# Note: Integration-tests will fail if these go out of sync
dar_lookup = {
    UUID("0a3f50c4-379f-32b8-e044-0003ba298018"): {
        "id": "0a3f50c4-379f-32b8-e044-0003ba298018",
        "vejnavn": "Skt. Johannes All\u00e9",
        "husnr": "2",
        "postnr": "8000",
        "postnrnavn": "Aarhus C",
        "kommunekode": "0751",
    },
    UUID("03c59320-1edd-40f4-9bbe-af135475205e"): {
        "id": "03c59320-1edd-40f4-9bbe-af135475205e",
        "vejnavn": "Julsøvej",
        "husnr": "14",
        "postnr": "8680",
        "postnrnavn": "Ry",
        "kommunekode": "0746",
    },
}
dar_parameterize = ("uuid,expected", list(dar_lookup.items()))
dar_non_existent = {
    UUID("00000000-0000-0000-0000-000000000000"),
    UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
}
# Actual DAR cleanse results
dar_cleanse_lookup = {
    "Sankt Johannes Alle 2, 8000 Aarhus C": {
        "kategori": "B",
        "resultater": [
            {
                "adresse": {
                    "id": "0a3f50c4-379f-32b8-e044-0003ba298018",
                    "vejnavn": "Skt.Johannes Alle",
                    "husnr": "2",
                    "postnr": "8000",
                    "postnrnavn": "Aarhus C",
                }
            }
        ],
    },
    "Rådhuspladsen 1, 8000 Aarhus C": {
        "kategori": "A",
        "resultater": [
            {
                "adresse": {
                    "id": "a79762e7-52bf-4199-a026-4ab42e1138a7",
                    "vejnavn": "Rådhuspladsen",
                    "husnr": "1",
                    "postnr": "8000",
                    "postnrnavn": "Aarhus C",
                }
            }
        ],
    },
    "Flyvervej x, Svendborg": {
        "kategori": "C",
        "resultater": [
            # ... Imagine lots of results here
        ],
    },
}
dar_cleanse_parameterize = (
    "address_string,expected",
    [
        (
            "Sankt Johannes Alle 2, 8000 Aarhus C",
            {
                "id": "0a3f50c4-379f-32b8-e044-0003ba298018",
                "vejnavn": "Skt.Johannes Alle",
                "husnr": "2",
                "postnr": "8000",
                "postnrnavn": "Aarhus C",
            },
        ),
        (
            "Rådhuspladsen 1, 8000 Aarhus C",
            {
                "id": "a79762e7-52bf-4199-a026-4ab42e1138a7",
                "vejnavn": "Rådhuspladsen",
                "husnr": "1",
                "postnr": "8000",
                "postnrnavn": "Aarhus C",
            },
        ),
    ],
)
dar_cleanse_unspecific_match = {"Flyvervej x, Svendborg", ""}


def assert_dar_response(result: dict, expected: dict) -> None:
    for key in expected.keys():
        assert result[key] == expected[key]


async def darserver_mock() -> web.Application:
    async def autocomplete(_: web.Request) -> web.Response:
        return web.Response(text="OK")

    async def cleanse_endpoint(request: web.Request) -> web.Response:
        address_string = request.query.get("betegnelse")
        if address_string not in dar_cleanse_lookup:
            raise web.HTTPNotFound()
        return web.json_response(dar_cleanse_lookup[address_string])

    async def single_address_endpoint(request: web.Request) -> web.Response:
        uuid = UUID(request.path.rsplit("/")[-1])
        if uuid not in dar_lookup:
            raise web.HTTPNotFound()
        return web.json_response(dar_lookup[uuid])

    async def address_endpoint(request: web.Request) -> web.Response:
        id = request.query.get("id")
        assert id is not None
        uuids = id.split("|")  # type: ignore
        uuids = map(UUID, uuids)  # type: ignore
        uuids = filter(lambda uuid: uuid in dar_lookup, uuids)  # type: ignore
        result = map(lambda uuid: dar_lookup[uuid], uuids)  # type: ignore
        return web.json_response(list(result))

    app = web.Application()
    app.router.add_get("/autocomplete", autocomplete)
    for addrtype in ALL_ADDRESS_TYPES:
        app.router.add_get(f"/{addrtype.value}/" + "{uuid}", single_address_endpoint)
        app.router.add_get(f"/{addrtype.value}", address_endpoint)

        app.router.add_get(f"/datavask/{addrtype.value}", cleanse_endpoint)
    return app


@pytest.fixture
async def darserver() -> web.Application:
    return await darserver_mock()


async def darclient_mocks(
    aiohttp_client: TestClient, darserver: web.Application
) -> Tuple[AsyncDARClient, DARClient]:
    class TestAsyncDARClient(AsyncDARClient):
        async def aopen(self) -> None:
            self._session = await aiohttp_client(darserver, timeout=ClientTimeout(2))  # type: ignore

    class TestDARClient(Syncable, TestAsyncDARClient):
        pass

    adarclient = TestAsyncDARClient()
    adarclient._baseurl = ""
    darclient = TestDARClient()
    darclient._baseurl = ""
    adarclient._fetch_single.retry.stop = stop_after_delay(0)  # type: ignore
    return adarclient, darclient  # type: ignore


async def darclient_mock(
    aiohttp_client: TestClient, darserver: web.Application
) -> DARClient:
    _, darclient = await darclient_mocks(aiohttp_client, darserver)
    return darclient


@pytest.fixture
async def darclient(
    aiohttp_client: TestClient, darserver: web.Application
) -> DARClient:
    return await darclient_mock(aiohttp_client, darserver)


async def adarclient_mock(
    aiohttp_client: TestClient, darserver: web.Application
) -> AsyncDARClient:
    adarclient, _ = await darclient_mocks(aiohttp_client, darserver)
    return adarclient


@pytest.fixture
async def adarclient(
    aiohttp_client: TestClient, darserver: web.Application
) -> AsyncDARClient:
    return await adarclient_mock(aiohttp_client, darserver)
