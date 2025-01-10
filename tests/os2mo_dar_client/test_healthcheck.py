# SPDX-FileCopyrightText: Magenta ApS
# SPDX-License-Identifier: MPL-2.0
from asyncio import sleep
from unittest.mock import MagicMock
from warnings import catch_warnings

import pytest
from aiohttp import ClientError
from aiohttp import web
from aiohttp.test_utils import TestClient
from more_itertools import first

from .utils import darclient_mock
from fastramqpi.os2mo_dar_client import DARClient


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


async def test_healthcheck_non_200(aiohttp_client: TestClient) -> None:
    # Non-200 status code
    status = {"entered": False}

    async def autocomplete_fail(_: web.Request) -> web.Response:
        status["entered"] = True
        raise web.HTTPInternalServerError()

    app = web.Application()
    app.router.add_get("/autocomplete", autocomplete_fail)
    darclient = await darclient_mock(aiohttp_client, app)
    async with darclient:
        result = await darclient.healthcheck()
    assert result is False
    assert status["entered"] is True


async def test_healthcheck_timeout(aiohttp_client: TestClient) -> None:
    # Timeout
    status = {"entered": False, "finished": False}

    async def autocomplete_slow(_: web.Request) -> web.Response:
        status["entered"] = True
        await sleep(5)
        status["finished"] = True
        return web.Response(text="OK")

    app = web.Application()
    app.router.add_get("/autocomplete", autocomplete_slow)
    darclient = await darclient_mock(aiohttp_client, app)
    async with darclient:
        result = await darclient.healthcheck(1)
    assert result is False
    assert status["entered"] is True
    assert status["finished"] is False


async def test_healthcheck_client_error(aiohttp_client: TestClient) -> None:
    # ClientError
    status = {"entered": False}

    async def autocomplete_never(_: web.Request) -> web.Response:
        status["entered"] = True
        return web.Response(text="OK")

    app = web.Application()
    app.router.add_get("/autocomplete", autocomplete_never)
    darclient = await darclient_mock(aiohttp_client, app)
    async with darclient:
        darclient._get_session().get = MagicMock(  # type: ignore
            side_effect=ClientError("BOOM")
        )
        result = await darclient.healthcheck(1)
    assert result is False
    assert status["entered"] is False
