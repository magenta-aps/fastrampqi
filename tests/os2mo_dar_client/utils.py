# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Tuple
from uuid import UUID

import pytest
from aiohttp import ClientTimeout
from aiohttp import web
from aiohttp.test_utils import TestClient
from tenacity import stop_after_delay

from fastramqpi.os2mo_dar_client import AddressType
from fastramqpi.os2mo_dar_client import AsyncDARClient
from fastramqpi.os2mo_dar_client import DARClient
from fastramqpi.os2mo_dar_client.dar_client import ALL_ADDRESS_TYPES
from fastramqpi.ra_utils.syncable import Syncable

Handler = Callable[[web.Request], Awaitable[web.Response]]


# Actual DAR replies from Adressevælgeren
# Note: Integration-tests will fail if these go out of sync
skt_johannes_alle_2: dict[str, Any] = {
    "id_lokalid": "0a3f5096-e43f-32b8-e044-0003ba298018",
    "husnummertekst": "2",
    "adgangsadressebetegnelse": "Skt. Johannes Allé 2, 8000 Aarhus C",
    "vejnavn": "Skt. Johannes Allé",
    "status": "3",
    "postnummer": {"navn": "Aarhus C", "postnr": "8000"},
    "navngivenvejkommunedel": {"kommune": "0751", "vejkode": "7425"},
    "supplerendebynavn": {"navn": None},
}
julsoevej_14: dict[str, Any] = {
    "id_lokalid": "0a3f5095-12d6-32b8-e044-0003ba298018",
    "husnummertekst": "14",
    "adgangsadressebetegnelse": "Julsøvej 14, 8680 Ry",
    "vejnavn": "Julsøvej",
    "status": "3",
    "postnummer": {"navn": "Ry", "postnr": "8680"},
    "navngivenvejkommunedel": {"kommune": "0746", "vejkode": "0499"},
    "supplerendebynavn": {"navn": None},
}
raadhuspladsen_1: dict[str, Any] = {
    "id_lokalid": "0a3f5096-c91e-32b8-e044-0003ba298018",
    "husnummertekst": "1",
    "adgangsadressebetegnelse": "Rådhuspladsen 1, 8000 Aarhus C",
    "vejnavn": "Rådhuspladsen",
    "status": "3",
    "postnummer": {"navn": "Aarhus C", "postnr": "8000"},
    "navngivenvejkommunedel": {"kommune": "0751", "vejkode": "7005"},
    "supplerendebynavn": {"navn": None},
}
adresser: dict[UUID, dict[str, Any]] = {
    UUID("0a3f50c4-379f-32b8-e044-0003ba298018"): {
        "id_lokalid": "0a3f50c4-379f-32b8-e044-0003ba298018",
        "adressebetegnelse": "Skt. Johannes Allé 2, 8000 Aarhus C",
        "etagebetegnelse": None,
        "doerbetegnelse": None,
        "status": "3",
        "husnummer": skt_johannes_alle_2,
    },
    UUID("03c59320-1edd-40f4-9bbe-af135475205e"): {
        "id_lokalid": "03c59320-1edd-40f4-9bbe-af135475205e",
        "adressebetegnelse": "Julsøvej 14, 8680 Ry",
        "etagebetegnelse": None,
        "doerbetegnelse": None,
        "status": "3",
        "husnummer": julsoevej_14,
    },
    UUID("0a3f50c4-05a3-32b8-e044-0003ba298018"): {
        "id_lokalid": "0a3f50c4-05a3-32b8-e044-0003ba298018",
        "adressebetegnelse": "Rådhuspladsen 1, 8000 Aarhus C",
        "etagebetegnelse": None,
        "doerbetegnelse": None,
        "status": "3",
        "husnummer": raadhuspladsen_1,
    },
}
husnumre: dict[UUID, dict[str, Any]] = {
    UUID(husnummer["id_lokalid"]): husnummer
    for husnummer in [skt_johannes_alle_2, julsoevej_14, raadhuspladsen_1]
}

# Expected (DAWA mini shaped) replies from the DAR client
dar_lookup: dict[UUID, dict[str, Any]] = {
    UUID("0a3f50c4-379f-32b8-e044-0003ba298018"): {
        "id": "0a3f50c4-379f-32b8-e044-0003ba298018",
        "vejnavn": "Skt. Johannes All\u00e9",
        "husnr": "2",
        "postnr": "8000",
        "postnrnavn": "Aarhus C",
        "kommunekode": "0751",
        "betegnelse": "Skt. Johannes All\u00e9 2, 8000 Aarhus C",
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
dar_cleanse_lookup = {
    "Sankt Johannes Alle 2, 8000 Aarhus C": {
        "vaskestatus": {
            "kode": 900,
            "tekst": "Vejnavn tilnærmet ift. stavevariationer. "
            "Eksakt husnummer og postnummer",
        },
        "vaskeresultat": {"adresse_id_lokalid": "0a3f50c4-379f-32b8-e044-0003ba298018"},
        "vaskeresultat_historisk": {"adressebetegnelse": None},
    },
    "Rådhuspladsen 1, 8000 Aarhus C": {
        "vaskestatus": {
            "kode": 1000,
            "tekst": "Eksakt match på vejnavn, husnummer og postnummer",
        },
        "vaskeresultat": {"adresse_id_lokalid": "0a3f50c4-05a3-32b8-e044-0003ba298018"},
        "vaskeresultat_historisk": {"adressebetegnelse": None},
    },
    "Flyvervej x, Svendborg": {
        "vaskestatus": {
            "kode": -1000,
            "tekst": "Tekst kan ikke genkendes som en adresse",
        },
        "vaskeresultat": {"adresse_id_lokalid": None},
        "vaskeresultat_historisk": {"adressebetegnelse": None},
    },
}
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


def assert_dar_response(result: dict, expected: dict) -> None:
    for key in expected.keys():
        assert result[key] == expected[key]


async def darserver_mock() -> web.Application:
    lookups = {
        AddressType.ADDRESS: ("adresse", "adresser", adresser),
        AddressType.ACCESS_ADDRESS: ("husnummer", "husnumre", husnumre),
    }

    def check_token(request: web.Request) -> None:
        if len(request.query.get("token", "")) < 10:
            raise web.HTTPBadRequest()

    async def search(request: web.Request) -> web.Response:
        check_token(request)
        return web.json_response([])

    async def cleanse_endpoint(request: web.Request) -> web.Response:
        check_token(request)
        address_string = request.query.get("adresse")
        if not address_string:
            raise web.HTTPBadRequest()
        return web.json_response(
            dar_cleanse_lookup.get(
                address_string,
                {
                    "vaskestatus": {
                        "kode": -1000,
                        "tekst": "Tekst kan ikke genkendes som en adresse",
                    },
                    "vaskeresultat": {"adresse_id_lokalid": None},
                    "vaskeresultat_historisk": {"adressebetegnelse": None},
                },
            )
        )

    def single_address_endpoint(addrtype: AddressType) -> Handler:
        key, _, lookup = lookups[addrtype]

        async def handler(request: web.Request) -> web.Response:
            check_token(request)
            uuid = UUID(request.match_info["uuid"])
            if uuid not in lookup:
                raise web.HTTPNotFound()
            return web.json_response({"status": "ok", key: lookup[uuid]})

        return handler

    def address_endpoint(addrtype: AddressType) -> Handler:
        _, key, lookup = lookups[addrtype]

        async def handler(request: web.Request) -> web.Response:
            check_token(request)
            ids = request.query.get("id_lokalids")
            assert ids is not None
            uuids = map(UUID, ids.split(","))
            result = [lookup[uuid] for uuid in uuids if uuid in lookup]
            if not result:
                raise web.HTTPNotFound()
            return web.json_response({"status": "ok", key: result})

        return handler

    app = web.Application()
    app.router.add_get("/adresser/soeg", search)
    app.router.add_get("/vask/", cleanse_endpoint)
    for addrtype in ALL_ADDRESS_TYPES:
        app.router.add_get(
            f"/{addrtype.value}/{{uuid}}", single_address_endpoint(addrtype)
        )
        app.router.add_get(f"/{addrtype.value}", address_endpoint(addrtype))
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
