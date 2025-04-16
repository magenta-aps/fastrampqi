# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from fastramqpi import depends
from fastramqpi.main import FastRAMQPI
from tests.fastramqpi.integration.conftest import Settings


@pytest.mark.integration_test
def test_database() -> None:
    """Test some database action."""

    class Base(DeclarativeBase):
        pass

    class User(Base):
        __tablename__ = "user"

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]

    settings = Settings()
    fastramqpi = FastRAMQPI(
        application_name="os2mo-test-integration",
        settings=settings.fastramqpi,
        graphql_version=22,
        database_metadata=Base.metadata,
    )
    fastramqpi.add_context(settings=settings)
    app = fastramqpi.get_app()

    @app.post("/add")
    async def add(session: depends.Session, name: str) -> None:
        session.add(User(name=name))

    @app.get("/get")
    async def get(session: depends.Session) -> list[str]:
        query = select(User.name)
        result = await session.scalars(query)
        return list(result)

    with TestClient(app) as client:
        assert client.post("/add?name=Alice").is_success
        assert client.post("/add?name=Bob").is_success
        assert client.get("/get").json() == ["Alice", "Bob"]
