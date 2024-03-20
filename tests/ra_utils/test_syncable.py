# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from asyncio import iscoroutinefunction
from asyncio import run
from inspect import isawaitable
from typing import Awaitable

import hypothesis.strategies as st
import pytest
from hypothesis import given

from ra_utils.syncable import Syncable


class AsyncAdder:
    async def add(self, a: int, b: int) -> int:
        return a + b


class Adder(Syncable, AsyncAdder):
    pass


async def acall_adder(*args) -> int:
    return await Adder().add(*args)


def call_adder(*args) -> int:
    return Adder().add(*args)  # type: ignore


async def acall_asyncadder(*args) -> int:
    return await AsyncAdder().add(*args)


def call_asyncadder(*args) -> Awaitable[int]:
    return AsyncAdder().add(*args)


@given(st.integers(), st.integers())
def test_add(a: int, b: int):
    assert iscoroutinefunction(AsyncAdder.add) is True
    assert iscoroutinefunction(Adder.add) is True

    expected = a + b

    # Calls to Adder
    result1 = run(acall_adder(a, b))
    assert isawaitable(result1) is False
    assert result1 == expected

    result2 = call_adder(a, b)
    assert isawaitable(result2) is False
    assert result2 == expected

    # Calls to AsyncAdder
    result3 = run(acall_asyncadder(a, b))
    assert isawaitable(result3) is False
    assert result3 == expected

    result4 = call_asyncadder(a, b)
    assert isawaitable(result4) is True
    assert run(result4) == expected  # type: ignore


class AsyncNoExitContext:
    def foo(self):
        return "bar"

    def __init__(self):
        self.inside = None

    async def __aenter__(self):
        self.inside = True
        return self


class ContextNoExit(Syncable, AsyncNoExitContext):
    pass  # Syncable must be first


class AsyncContext(AsyncNoExitContext):
    async def __aexit__(self, *err):
        self.inside = False


class Context(Syncable, AsyncContext):
    pass  # Syncable must be first


async def acall_context() -> None:
    context = Context()
    assert context.inside is None
    async with context:
        assert context.inside is True
    assert context.inside is False


def call_context() -> None:
    context = Context()
    assert context.inside is None
    with context:
        assert context.inside is True
    assert context.inside is False


async def acall_asynccontext() -> None:
    context = AsyncContext()
    assert context.inside is None
    async with context:
        assert context.inside is True
    assert context.inside is False


def call_asynccontext() -> None:
    context = AsyncContext()
    assert context.inside is None
    # No __enter__, but __aenter__ exists
    with pytest.raises(AttributeError) as excinfo:
        with context:  # type: ignore
            assert context.inside is True
    assert "__enter__" in str(excinfo)
    assert hasattr(context, "__aenter__") is True
    assert context.inside is None


def test_context():
    # Calls to Context
    run(acall_context())
    call_context()

    # Calls to AsyncContext
    run(acall_asynccontext())
    call_asynccontext()

    # Check with no __aenter__ at all
    with pytest.raises(AttributeError) as excinfo:
        with Adder():
            pass
    assert "__enter__" in str(excinfo)

    # Check with no __aenter__ at all
    with pytest.raises(AttributeError) as excinfo:
        with ContextNoExit():
            pass
    assert "__exit__" in str(excinfo)

    assert ContextNoExit().foo() == "bar"
