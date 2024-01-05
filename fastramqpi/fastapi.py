# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
"""FastAPI Framework."""
import logging
from collections.abc import Awaitable
from collections.abc import Callable
from contextlib import asynccontextmanager
from contextlib import AsyncExitStack
from contextlib import suppress
from functools import partial
from typing import Any
from typing import AsyncContextManager
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

from .config import FastAPIIntegrationSystemSettings
from .context import Context
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

    context: dict[str, Any] = request.state.context
    healthchecks = context["healthchecks"]

    async def check(healthcheck: Callable[[dict], Awaitable[bool]]) -> bool:
        with suppress(Exception):
            return await healthcheck(context)
        return False

    healthstatus = {}
    for name, healthcheck in healthchecks.items():
        healthstatus[name] = await check(healthcheck)

    if not all(healthstatus.values()):
        status_code = HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=healthstatus, status_code=status_code)


@asynccontextmanager
async def _lifespan(app: FastAPI, context: Context) -> AsyncIterator[dict]:
    """ASGI lifespan context handler.

    Runs all the configured lifespan managers according to their priority.

    Returns:
        None
    """
    async with AsyncExitStack() as stack:
        lifespan_managers = context["lifespan_managers"]
        for _, priority_set in sorted(lifespan_managers.items()):
            for lifespan_manager in priority_set:
                await stack.enter_async_context(lifespan_manager)
        yield {
            "context": context,
        }


class FastAPIIntegrationSystem:
    """FastAPI-based integration framework.

    Motivated by a lot of shared code between our integrations.
    """

    def __init__(
        self, application_name: str, settings: FastAPIIntegrationSystemSettings
    ) -> None:
        super().__init__()
        self.settings = settings

        configure_logging(self.settings.log_level)

        # Setup shared context
        self._context: Context = {
            "name": application_name,
            "settings": self.settings,
            "healthchecks": {},
            "lifespan_managers": {},
            "user_context": {},
        }

        # Setup FastAPI
        app = FastAPI(
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
            lifespan=partial(_lifespan, context=self._context),
        )
        app.include_router(fastapi_router)
        # Expose Metrics
        if self.settings.enable_metrics:
            # Update metrics info
            update_build_information(
                version=self.settings.commit_tag, build_hash=self.settings.commit_sha
            )

            Instrumentator().instrument(app).expose(app)
        self.app = app
        self._context["app"] = self.app

    def add_lifespan_manager(
        self, manager: AsyncContextManager, priority: int = 1000
    ) -> None:
        """Add the provided life-cycle manager to the ASGI lifespan context.

        Args:
            manager: The manager to add.
            priority: The priority of the manager, lowest priorities are run first.

        Returns:
            None
        """

        priority_set = self._context["lifespan_managers"].setdefault(priority, set())
        priority_set.add(manager)

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
        if name in self._context["healthchecks"]:
            raise ValueError("Name already used")
        self._context["healthchecks"][name] = healthcheck

    def add_context(self, **kwargs: Any) -> None:
        """Add the provided key-value pair to the user-context.

        The added key-value pair will be available under context["user_context"].

        Args:
            key: The key to add under.
            value: The value to add.

        Returns:
            None
        """
        self._context["user_context"].update(**kwargs)

    def get_context(self) -> Context:
        """Return the contained context.

        Returns:
            The contained context.
        """
        return self._context

    def get_app(self) -> FastAPI:
        """Return the contained FastAPI application.

        Returns:
            FastAPI application.
        """
        return self.app
