# SPDX-FileCopyrightText: Magenta ApS
# SPDX-License-Identifier: MPL-2.0
from collections.abc import Iterator
from typing import Any

import pytest
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseSettings
from pydantic import Field

from fastramqpi.config import Settings as FastRAMQPISettings
from fastramqpi.depends import UserContext
from fastramqpi.main import FastRAMQPI
from fastramqpi.ramqp.depends import RateLimit
from fastramqpi.ramqp.mo import MORouter
from fastramqpi.ramqp.mo import PayloadUUID


@pytest.fixture
def test_app() -> FastAPI:
    """Create FastAPI test app.

    NOTE: This MUST follow the example from the README very closely -- that's exactly
    what we want to test works.
    """

    class Settings(BaseSettings):
        class Config:
            frozen = True
            env_nested_delimiter = "__"

        fastramqpi: FastRAMQPISettings = Field(
            default_factory=FastRAMQPISettings, description="FastRAMQPI settings"
        )

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

    return create_app()


@pytest.fixture
def test_client(test_app: FastAPI) -> Iterator[TestClient]:
    """Create ASGI test client with associated lifecycles."""
    with TestClient(test_app) as client:
        yield client


class FakeAutogeneratedGraphQLClient:
    def __init__(self, mo_client: AsyncOAuth2Client):
        self.mo_client = mo_client

    async def _testing__get_employee(self, cpr_number: str) -> dict[str, Any]:
        query = """
            query _Testing_GetEmployee($cpr_number: CPR!) {
              employees(filter: {cpr_numbers: [$cpr_number]}) {
                objects {
                  objects {
                    uuid
                    cpr_number
                    given_name
                  }
                }
              }
            }
        """
        r = await self.mo_client.post(
            "/graphql/v20",
            json=dict(
                query=query,
                variables={
                    "cpr_number": cpr_number,
                },
            ),
        )
        # ariadne returns the 'employee' field directly when it is the only one
        employees = r.json()["data"]["employees"]
        assert isinstance(employees, dict)
        return employees

    async def _testing__create_employee(self, cpr_number: str) -> dict[str, Any]:
        query = """
            mutation _Testing_CreateEmployee($cpr_number: CPR!) {
              employee_create(
                input: {
                  given_name: "Alice",
                  surname: "Nielsen",
                  cpr_number: $cpr_number,
                }
              ) {
                objects {
                  uuid
                }
              }
            }
        """
        r = await self.mo_client.post(
            "/graphql/v20",
            json=dict(
                query=query,
                variables={
                    "cpr_number": cpr_number,
                },
            ),
        )
        # ariadne returns the 'employee_create' field directly when it is the only one
        employees = r.json()["data"]["employee_create"]
        assert isinstance(employees, dict)
        return employees


@pytest.fixture
async def graphql_client(test_client: TestClient) -> FakeAutogeneratedGraphQLClient:
    """Fake authenticated GraphQL codegen client for OS2mo.

    We don't use an autogenerated codegen client here to avoid polluting the repo.
    """
    mo_client = test_client.app_state["context"]["mo_client"]
    return FakeAutogeneratedGraphQLClient(mo_client)
