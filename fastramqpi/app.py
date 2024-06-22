# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
"""FastAPI Framework."""
from contextlib import asynccontextmanager
from contextlib import AsyncExitStack
from functools import partial
from typing import Any
from typing import AsyncContextManager
from typing import AsyncIterator

from fastapi import FastAPI

from .config import FastAPIIntegrationSystemSettings
from .context import Context
from .context import HealthcheckFunction
from .fastintegration import FastIntegration


@asynccontextmanager
async def _lifespan(app: FastIntegration, context: Context) -> AsyncIterator[dict]:
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
        self.settings = settings

        # Setup shared context
        self._context: Context = {
            "name": application_name,
            "settings": self.settings,
            "healthchecks": {},
            "lifespan_managers": {},
            "user_context": {},
        }

        # Setup FastAPI
        app = FastIntegration(
            application_name,
            settings,
            lifespan=partial(_lifespan, context=self._context),
        )
        app.state.context = self._context
        self._context["instrumentator"] = app.instrumentator
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
        self.app.add_healthcheck(name, healthcheck)

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
