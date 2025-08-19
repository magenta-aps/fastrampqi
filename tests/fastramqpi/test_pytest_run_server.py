# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from contextlib import suppress

import pytest
from fastapi import FastAPI
from httpx import ConnectError

from fastramqpi.pytest_plugin import run_server
from fastramqpi.pytest_plugin import run_test_client

# Test FastAPI "Hello World" app
app = FastAPI()


@app.get("/")
def index() -> str:
    return "Hello World"


async def check_http_request() -> None:
    async with run_test_client() as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.text == '"Hello World"'


async def test_run_server() -> None:
    # Before the server started our HTTP call fails
    with pytest.raises(ConnectError) as exc_info:
        await check_http_request()
    assert "All connection attempts failed" in str(exc_info.value)

    # When the server is running our HTTP calls succeed
    async with run_server(app):
        await check_http_request()

    # After the server shutdown our HTTP call fails
    with pytest.raises(ConnectError) as exc_info:
        await check_http_request()
    assert "All connection attempts failed" in str(exc_info.value)


async def test_run_server_restarts() -> None:
    # Do multiple startups and shutdowns checking our request works each time
    for _ in range(3):
        async with run_server(app):
            await check_http_request()


async def test_run_server_exception() -> None:
    with suppress(ValueError):
        # Server should shutdown gracefully even if an exception occurs
        async with run_server(app):
            await check_http_request()
            raise ValueError("BOOM")

    # After the server shutdown our HTTP call should fail
    # If it does not, it means the server is still running
    with pytest.raises(ConnectError) as exc_info:
        await check_http_request()
    assert "All connection attempts failed" in str(exc_info.value)

    # Even if a previous server run failed, we should be able to restart
    async with run_server(app):
        await check_http_request()
