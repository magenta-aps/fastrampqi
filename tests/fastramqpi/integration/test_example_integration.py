# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any
from typing import Iterator
from uuid import UUID

import pytest
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.testclient import TestClient
from more_itertools import one

from fastramqpi.depends import UserContext
from fastramqpi.main import FastRAMQPI
from fastramqpi.pytest_util import retry
from fastramqpi.ramqp.depends import RateLimit
from fastramqpi.ramqp.mo import MORouter
from fastramqpi.ramqp.mo import PayloadUUID
from tests.fastramqpi.integration.conftest import FakeAutogeneratedGraphQLClient
from tests.fastramqpi.integration.conftest import Settings


@pytest.fixture
def test_client() -> Iterator[TestClient]:
    """Create FastAPI ASGI test client with associated lifecycles.

    NOTE: This MUST follow the example from the README very closely -- that's exactly
    what we want to test works.
    """
    fastapi_router = APIRouter()
    amqp_router = MORouter()

    @amqp_router.register("person")
    async def listen_to_persons(
        user_context: UserContext, uuid: PayloadUUID, _: RateLimit
    ) -> None:
        user_context["uuid"] = uuid

    def create_fastramqpi(**kwargs: Any) -> FastRAMQPI:
        settings = Settings(**kwargs)
        fastramqpi = FastRAMQPI(
            application_name="os2mo-test-integration",
            settings=settings.fastramqpi,
            graphql_version=20,
        )
        fastramqpi.add_context(settings=settings)

        # Add our AMQP router(s)
        amqpsystem = fastramqpi.get_amqpsystem()
        amqpsystem.router.registry.update(amqp_router.registry)

        # Add our FastAPI router(s)
        app = fastramqpi.get_app()
        app.include_router(fastapi_router)

        return fastramqpi

    def create_app(**kwargs: Any) -> FastAPI:
        fastramqpi = create_fastramqpi(**kwargs)
        return fastramqpi.get_app()

    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.mark.integration_test
async def test_create_person(
    test_client: TestClient,
    graphql_client: FakeAutogeneratedGraphQLClient,
) -> None:
    """Test pytest integration plugin.

    NOTE: This MUST follow the example from the README very closely -- that's exactly
    what we want to test works.
    """
    # Precondition: The person does not already exist.
    cpr_number = "0711909893"  # 0.37% chance of being emil's
    employee = await graphql_client._testing__get_employee(cpr_number)
    assert employee == {"objects": []}

    # Trigger integration to create the employee
    await graphql_client._testing__create_employee(cpr_number)

    @retry()
    async def verify() -> None:
        # Check that the employee was created
        employees = await graphql_client._testing__get_employee(cpr_number)
        employee_states = one(employees["objects"])
        employee = one(employee_states["objects"])
        assert employee["cpr_number"] == cpr_number
        assert employee["given_name"] == "Alice"
        # Check that we received an AMQP event
        user_context = test_client.app_state["context"]["user_context"]
        assert user_context["uuid"] == UUID(employee["uuid"])

    await verify()
