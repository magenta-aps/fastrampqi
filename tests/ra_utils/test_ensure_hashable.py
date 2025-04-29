# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from decimal import Decimal
from typing import Any
from typing import Callable

import pytest
from hypothesis import assume
from hypothesis import given
from hypothesis import strategies as st

from fastramqpi.ra_utils.ensure_hashable import ensure_hashable
from fastramqpi.ra_utils.ensure_hashable import is_hashable
from fastramqpi.ra_utils.ensure_hashable import is_probably_hashable

from .utils import any_strategy


class Unhashable:
    def __hash__(self) -> int:
        raise TypeError("Not hashable")


@pytest.mark.parametrize(
    "check_func,value,hashable",
    [
        [is_hashable, 0, True],
        [is_probably_hashable, 0, True],
        [is_hashable, "a", True],
        [is_probably_hashable, "a", True],
        [is_hashable, 13.6, True],
        [is_probably_hashable, 13.6, True],
        [is_hashable, (2,), True],
        [is_probably_hashable, (2,), True],
        [is_hashable, Decimal("NaN"), True],
        [is_probably_hashable, Decimal("NaN"), True],
        [is_hashable, [], False],
        [is_probably_hashable, [], False],
        [is_hashable, {}, False],
        [is_probably_hashable, {}, False],
        [is_hashable, set(), False],
        [is_probably_hashable, set(), False],
        [is_probably_hashable, Decimal("sNaN"), True],
        [is_hashable, Decimal("sNaN"), False],
        [is_probably_hashable, Unhashable(), True],
        [is_hashable, Unhashable(), False],
    ],
)
def test_is_hashable(check_func: Callable, value: int, hashable: bool) -> None:
    assert check_func(value) == hashable


@given(value=any_strategy)
def test_ensure_hashable(value: Any) -> None:
    assume(not isinstance(value, slice))
    hashable = ensure_hashable(value)
    hash(hashable)


@given(value=st.slices(1))
def test_slice_unhashable(value: Any) -> None:
    with pytest.raises(TypeError) as exc_info:
        ensure_hashable(value)
    assert "slice cannot be made hashable" in str(exc_info.value)


def test_unhashable_class_unhashable() -> None:
    value = Unhashable()
    with pytest.raises(TypeError) as exc_info:
        ensure_hashable(value)
    assert "is not hashable, please report this!" in str(exc_info.value)


def test_signalling_nan_to_quiet_nan() -> None:
    value = Decimal("sNaN")
    new_value = ensure_hashable(value)
    assert new_value.is_qnan()
