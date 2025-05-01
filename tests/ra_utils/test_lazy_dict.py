# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from functools import partial
from typing import TypeVar
from unittest import TestCase

import hypothesis.strategies as st
from hypothesis import given

from fastramqpi.ra_utils.lazy_dict import LazyDict
from fastramqpi.ra_utils.lazy_dict import LazyEval
from fastramqpi.ra_utils.lazy_dict import LazyEvalBare
from fastramqpi.ra_utils.lazy_dict import LazyEvalDerived

T = TypeVar("T")


def exception_func() -> None:
    """Function that always throws an exception."""
    raise ValueError()


def identity_func(x: T) -> T:
    """Function that always returns its argument."""
    return x


class LazyDictTests(TestCase):
    """Test LazyDict functions as expected."""

    def setUp(self) -> None:
        self.counter = 0

        def counter_func() -> int:
            self.counter += 1
            return self.counter

        self.counter_func = counter_func

    @given(st.dictionaries(st.text(), st.text()))
    def test_ordinary_dict_functionality(self, dicty: dict) -> None:
        """Test that LazyDict functions similar to an ordinary dict."""
        lazy_dict = LazyDict(dicty)

        self.assertEqual(dicty.items(), lazy_dict.items())
        self.assertEqual(len(dicty), len(lazy_dict))
        self.assertEqual(str(dicty), str(lazy_dict))
        self.assertEqual(repr(dicty), repr(lazy_dict))

        for key in dicty.keys():
            self.assertEqual(dicty[key], lazy_dict[key])

    def test_lazy_evalulation_bare(self) -> None:
        """Test that LazyDict supports lazy evaluation using LazyEvalBare."""
        lazy_dict: LazyDict = LazyDict({"exception_func": LazyEvalBare(exception_func)})
        with self.assertRaises(ValueError):
            lazy_dict["exception_func"]

        identity_lambda = lambda x: x  # noqa: E731
        lazy_dict["identity_func1"] = LazyEvalBare(partial(identity_lambda, 2))
        self.assertEqual(lazy_dict["identity_func1"], 2)
        self.assertEqual(lazy_dict["identity_func1"], 2)

        lazy_dict["identity_func2"] = LazyEvalBare(partial(identity_func, 4))
        self.assertEqual(lazy_dict["identity_func2"], 4)
        self.assertEqual(lazy_dict["identity_func2"], 4)

        lazy_dict["identity_func3"] = LazyEvalBare(lambda: 8)
        self.assertEqual(lazy_dict["identity_func3"], 8)
        self.assertEqual(lazy_dict["identity_func3"], 8)

        lazy_dict["c_no_cache"] = LazyEvalBare(self.counter_func)
        self.assertEqual(lazy_dict["c_no_cache"], 1)
        self.assertEqual(lazy_dict["c_no_cache"], 1)

        lazy_dict["c_cache"] = LazyEvalBare(self.counter_func, cache=False)
        self.assertEqual(lazy_dict["c_cache"], 2)
        self.assertEqual(lazy_dict["c_cache"], 3)
        self.assertEqual(lazy_dict["c_no_cache"], 1)
        self.assertEqual(lazy_dict["c_cache"], 4)

    def test_lazy_evalulation_normal(self) -> None:
        """Test that LazyDict supports lazy evaluation using LazyEval."""
        lazy_dict = LazyDict({"base_value": 5})
        lazy_dict["derived_func1"] = LazyEval(
            lambda key, dictionary: dictionary["base_value"]
        )
        self.assertEqual(lazy_dict["derived_func1"], 5)
        self.assertEqual(lazy_dict["derived_func1"], 5)
        lazy_dict["base_value"] = 3
        self.assertEqual(lazy_dict["derived_func1"], 5)
        self.assertEqual(lazy_dict["derived_func1"], 5)

        lazy_dict["derived_func2"] = LazyEval(
            lambda key, dictionary: dictionary["base_value"], cache=False
        )
        self.assertEqual(lazy_dict["derived_func2"], 3)
        self.assertEqual(lazy_dict["derived_func2"], 3)
        lazy_dict["base_value"] = 1
        self.assertEqual(lazy_dict["derived_func2"], 1)
        self.assertEqual(lazy_dict["derived_func2"], 1)

    def test_lazy_evalulation_derived(self) -> None:
        """Test that LazyDict supports lazy evaluation using LazyEvalDerived."""
        lazy_dict = LazyDict({"base_value": 5})
        lazy_dict["derived_func1"] = LazyEvalDerived(lambda base_value: base_value)
        self.assertEqual(lazy_dict["derived_func1"], 5)
        lazy_dict["base_value"] = 3
        self.assertEqual(lazy_dict["derived_func1"], 5)

        lazy_dict["derived_func2"] = LazyEvalDerived(
            lambda base_value: base_value, cache=False
        )
        self.assertEqual(lazy_dict["derived_func2"], 3)
        lazy_dict["base_value"] = 1
        self.assertEqual(lazy_dict["derived_func2"], 1)

        lazy_dict["derived_func3"] = LazyEvalDerived(
            lambda derived_func1, derived_func2: derived_func1 + derived_func2,
            cache=False,
        )
        self.assertEqual(lazy_dict["derived_func3"], 5 + 1)
        lazy_dict["base_value"] = 2
        self.assertEqual(lazy_dict["derived_func3"], 5 + 2)
