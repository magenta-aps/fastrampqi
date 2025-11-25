# SPDX-FileCopyrightText: Magenta ApS
# SPDX-License-Identifier: MPL-2.0
import re

import pytest
import structlog
from fastapi.testclient import TestClient

from fastramqpi.main import FastRAMQPI
from tests.fastramqpi.integration.conftest import Settings

logger = structlog.stdlib.get_logger()


@pytest.mark.integration_test
def test_request_id_middleware(capsys: pytest.CaptureFixture[str]) -> None:
    settings = Settings()
    fastramqpi = FastRAMQPI(
        application_name="os2mo-test-integration",
        settings=settings.fastramqpi,
        graphql_version=22,
    )
    app = fastramqpi.get_app()

    @app.get("/hello")
    async def hello() -> None:
        logger.info("Hello, world!")

    with TestClient(app) as client:
        # Requst ID unset
        client.get("/hello")
        assert re.search(
            r'^{"event": "Hello, world!", "request_id": "[0-9a-f\-]{36}", "logger": "tests.fastramqpi.integration.test_middleware", "level": "info"}$',
            capsys.readouterr().err,
            flags=re.MULTILINE,
        )

        # Request ID explicitly set
        client.get("/hello", headers={"X-Request-ID": "foo"})
        assert re.search(
            r'^{"event": "Hello, world!", "request_id": "foo", "logger": "tests.fastramqpi.integration.test_middleware", "level": "info"}$',
            capsys.readouterr().err,
            flags=re.MULTILINE,
        )


@pytest.mark.integration_test
def test_exception_middleware(capsys: pytest.CaptureFixture[str]) -> None:
    settings = Settings()
    fastramqpi = FastRAMQPI(
        application_name="os2mo-test-integration",
        settings=settings.fastramqpi,
        graphql_version=22,
    )
    app = fastramqpi.get_app()

    @app.get("/error")
    async def error() -> float:
        raise ArithmeticError("Negative bank balance after rent! Eat the rich!")

    with TestClient(app) as client:
        r = client.get("/error")
        assert "ArithmeticError" in r.text
        assert "ArithmeticError" in capsys.readouterr().err
