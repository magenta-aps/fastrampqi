# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple
from unittest import TestCase

import hypothesis.strategies as st
from hypothesis import given

from fastramqpi.ra_utils.apply import apply
from fastramqpi.ra_utils.apply import has_self_arg


class Classy:
    def method(self):
        pass

    @classmethod
    def classmethod(cls):
        pass

    @staticmethod
    def staticmethod():
        pass


def function():
    pass


def test_has_self_arg():
    classy = Classy()
    assert has_self_arg(classy.method) is False
    assert has_self_arg(classy.classmethod) is False
    assert has_self_arg(classy.staticmethod) is False
    assert has_self_arg(Classy.method) is True
    assert has_self_arg(Classy.classmethod) is False
    assert has_self_arg(Classy.staticmethod) is False
    assert has_self_arg(function) is False


@apply
def add2tup(a: int, b: int) -> int:
    return a + b


@apply
def add3tup(a: int, b: int, c: int) -> int:
    return a + b + c


def add2(a: int, b: int) -> int:
    return a + b


def add3(a: int, b: int, c: int) -> int:
    return a + b + c


class ApplyTests(TestCase):
    """Test the apply function works as expected."""

    @apply
    def add2tup(self, a: int, b: int):
        return a + b

    @apply
    def add3tup(self, a: int, b: int, c: int):
        return a + b + c

    def add2(self, a: int, b: int):
        return a + b

    def add3(self, a: int, b: int, c: int):
        return a + b + c

    @given(st.tuples(st.integers(), st.integers()))
    def test_apply_add2(self, tup: Tuple[int, int]):
        """Test that two tuples are applied correctly."""
        expected = tup[0] + tup[1]

        result = apply(add2)(tup)
        self.assertEqual(result, expected)

        result = apply(self.add2)(tup)
        self.assertEqual(result, expected)

        result = add2tup(tup)
        self.assertEqual(result, expected)

        result = self.add2tup(tup)
        self.assertEqual(result, expected)

    @given(st.tuples(st.integers(), st.integers(), st.integers()))
    def test_apply_add3(self, tup: Tuple[int, int, int]):
        """Test that three tuples are applied correctly."""
        expected = tup[0] + tup[1] + tup[2]

        result = apply(add3)(tup)
        self.assertEqual(result, expected)

        result = apply(self.add3)(tup)
        self.assertEqual(result, expected)

        result = add3tup(tup)
        self.assertEqual(result, expected)

        result = self.add3tup(tup)
        self.assertEqual(result, expected)
