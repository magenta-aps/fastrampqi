# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Annotated
from typing import AsyncIterable
from typing import Iterable
from unittest.mock import MagicMock
from unittest.mock import create_autospec
from unittest.mock import sentinel

from fastapi import Depends

from fastramqpi import depends
from fastramqpi.context import Context
from fastramqpi.depends import from_user_context
from fastramqpi.ramqp.depends import dependency_injected
from fastramqpi.ramqp.depends import dependency_injected_with_deps


async def test_depends() -> None:
    """Test depends."""

    async def handler(
        mo_amqp_system: depends.MOAMQPSystem,
        legacy_graphql_client: depends.LegacyGraphQLClient,
        legacy_graphql_session: depends.LegacyGraphQLSession,
        legacy_model_client: depends.LegacyModelClient,
        mo_client: depends.MOClient,
        user_context: depends.UserContext,
        user_context_a: Annotated[int, Depends(from_user_context("a"))],
    ) -> None:
        pass

    mock_handler = create_autospec(handler)

    context: Context = {
        "amqpsystem": sentinel.amqpsystem,
        "legacy_graphql_client": sentinel.graphql_client,
        "legacy_graphql_session": sentinel.graphql_session,
        "legacy_model_client": sentinel.model_client,
        "mo_client": sentinel.mo_client,
        "user_context": {
            "a": 1,
        },
    }
    await dependency_injected(mock_handler)(message=MagicMock(), context=context)

    mock_handler.assert_awaited_once_with(
        mo_amqp_system=sentinel.amqpsystem,
        legacy_graphql_client=sentinel.graphql_client,
        legacy_graphql_session=sentinel.graphql_session,
        legacy_model_client=sentinel.model_client,
        mo_client=sentinel.mo_client,
        user_context={"a": 1},
        user_context_a=1,
    )


async def test_extra_dependencies() -> None:
    """Test extra depends."""

    async def handler(
        mo_client: depends.MOClient,
    ) -> None:
        pass

    result = {}

    def sync_deps(user_context: depends.UserContext) -> None:
        result["sync_deps"] = user_context["a"]

    async def async_deps(user_context: depends.UserContext) -> None:
        result["async_deps"] = user_context["a"]

    def sync_yield_deps(user_context: depends.UserContext) -> Iterable[None]:
        result["sync_yield_deps"] = {}
        result["sync_yield_deps"]["before"] = user_context["a"]
        yield
        result["sync_yield_deps"]["after"] = user_context["a"]

    async def async_yield_deps(
        user_context: depends.UserContext,
    ) -> AsyncIterable[None]:
        result["async_yield_deps"] = {}
        result["async_yield_deps"]["before"] = user_context["a"]
        yield
        result["async_yield_deps"]["after"] = user_context["a"]

    mock_handler = create_autospec(handler)

    context: Context = {
        "amqpsystem": sentinel.amqpsystem,
        "legacy_graphql_client": sentinel.graphql_client,
        "legacy_graphql_session": sentinel.graphql_session,
        "legacy_model_client": sentinel.model_client,
        "mo_client": sentinel.mo_client,
        "user_context": {
            "a": 1,
        },
    }
    await dependency_injected_with_deps(
        mock_handler,
        dependencies=[
            Depends(sync_deps),
            Depends(async_deps),
            Depends(sync_yield_deps),
            Depends(async_yield_deps),
        ],
    )(
        message=MagicMock(),
        context=context,
    )

    assert result == {
        "sync_deps": 1,
        "async_deps": 1,
        "sync_yield_deps": {"before": 1, "after": 1},
        "async_yield_deps": {"before": 1, "after": 1},
    }

    mock_handler.assert_awaited_once_with(
        mo_client=sentinel.mo_client,
    )


async def test_from_user_context_caching() -> None:
    """Test that from_user_context always returns the exact same inner function."""
    assert from_user_context("a") == from_user_context("a")
    assert from_user_context("a") != from_user_context("b")
    assert from_user_context("b") == from_user_context("b")

    assert id(from_user_context("a")) == id(from_user_context("a"))
    assert id(from_user_context("a")) != id(from_user_context("b"))
    assert id(from_user_context("b")) == id(from_user_context("b"))
