# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
"""FastIntegration."""
import logging
from collections.abc import Awaitable
from collections.abc import Callable
from contextlib import asynccontextmanager
from contextlib import suppress
from functools import partial
from typing import Any
from typing import AsyncIterator

import structlog
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from prometheus_client import Info
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.status import HTTP_200_OK
from starlette.status import HTTP_204_NO_CONTENT
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE
from starlette.types import Lifespan
from fastapi.applications import AppType

from .config import FastAPIIntegrationSystemSettings
from .context import HealthcheckFunction


logger = structlog.get_logger()
fastapi_router = APIRouter()
build_information = Info("build_information", "Build information")


def update_build_information(version: str, build_hash: str) -> None:
    """Update build information.

    Args:
        version: The version to set.
        build_hash: The build hash to set.

    Returns:
        None.
    """
    build_information.info(
        {
            "version": version,
            "hash": build_hash,
        }
    )


def configure_logging(log_level_name: str) -> None:
    """Setup our logging.

    Args:
        log_level_name: The logging level.

    Returns:
        None
    """
    log_level_value = logging.getLevelName(log_level_name)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(log_level_value)
    )


@fastapi_router.get("/")
async def index(request: Request) -> dict[str, str]:
    """Endpoint to return name of integration."""
    context: dict[str, Any] = request.state.context
    return {"name": context["name"]}


@fastapi_router.get("/health/ready", status_code=HTTP_204_NO_CONTENT)
async def readiness() -> None:
    """Endpoint to be used as a readiness probe for Kubernetes."""
    # TODO: Remove once everyone is using v1.4.3+
    return None


@fastapi_router.get(
    "/health/live",
    status_code=HTTP_200_OK,
    responses={
        "200": {"description": "Ready"},
        "503": {"description": "Not ready"},
    },
)
async def liveness(request: Request) -> JSONResponse:
    """Endpoint to be used as a liveness probe for Kubernetes."""
    status_code = HTTP_200_OK

    healthchecks: dict[str, HealthcheckFunction] = request.app.state.healthchecks

    async def check(healthcheck: Callable[[dict], Awaitable[bool]]) -> bool:
        with suppress(Exception):
            return await healthcheck(request.state)
        return False

    healthstatus = {}
    for name, healthcheck in healthchecks.items():
        healthstatus[name] = await check(healthcheck)

    if not all(healthstatus.values()):
        status_code = HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=healthstatus, status_code=status_code)


def enable_debugging() -> None:  # pragma: no cover
    import debugpy  # type: ignore

    logger.debug("Enabling debugging", port=5678)
    debugpy.listen(("0.0.0.0", 5678))


@asynccontextmanager
async def _lifespan_wrapper(app: "FastIntegration", lifespan: Lifespan[AppType]) -> AsyncIterator[dict]:
    async with lifespan(app) as dicty:
        app.state = dicty
        yield dicty


class FastIntegration(FastAPI):

    def __init__(
        self,
        application_name: str,
        settings: FastAPIIntegrationSystemSettings,
        lifespan: Lifespan[AppType] | None = None,
        **kwargs: Any,
    ) -> None:
        self.settings = settings

        configure_logging(self.settings.log_level)

        if self.settings.dap:  # pragma: no cover
            enable_debugging()

        wrapped_lifespan = None
        if lifespan is not None:
            wrapped_lifespan = partial(_lifespan_wrapper, lifespan=lifespan)

        super().__init__(
            title=application_name,
            version=self.settings.commit_tag,
            contact={
                "name": "Magenta Aps",
                "url": "https://www.magenta.dk/",
                "email": "info@magenta.dk",
            },
            license_info={
                "name": "MPL-2.0",
                "url": "https://www.mozilla.org/en-US/MPL/2.0/",
            },
            lifespan=wrapped_lifespan,
            **kwargs,
        )
        self.state.healthchecks = {}
        super().include_router(fastapi_router)
        # Expose Metrics
        self.instrumentator = None
        if self.settings.enable_metrics:
            # Update metrics info
            update_build_information(
                version=self.settings.commit_tag, build_hash=self.settings.commit_sha
            )
            self.instrumentator = Instrumentator()
            self.instrumentator.instrument(self).expose(self)

    def add_healthcheck(self, name: str, healthcheck: HealthcheckFunction) -> None:
        """Add the provided healthcheck to the Kubernetes readiness probe.

        Args:
            name: Name of the healthcheck to add.
            healthcheck: The healthcheck callback function.

        Raises:
            ValueError: If the name has already been used.

        Returns:
            None
        """
        if name in self.state.healthchecks:
            raise ValueError("Name already used")
        self.state.healthchecks[name] = healthcheck
