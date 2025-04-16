# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from difflib import SequenceMatcher
from functools import reduce
from typing import Any
from unittest import TestCase

import hypothesis.strategies as st
from hypothesis import assume
from hypothesis import event
from hypothesis import example
from hypothesis import given
from hypothesis import target

from fastramqpi.ra_utils.multiple_replace import multiple_replace


def similar(a: str, b: str) -> float:
    """Return how similar a and b are.

    Returns:
        float: 1 on perfectly identical strings, 0 on asimilar strings.
    """
    return SequenceMatcher(None, a, b).ratio()


@st.composite
def draw_text_and_substring(draw: Any, substring_max_size: int) -> tuple:
    text = draw(st.text(min_size=1))
    substring_length = draw(st.integers(min_value=1, max_value=substring_max_size))
    assume(len(text) - substring_length > 0)

    idx = draw(st.integers(min_value=0, max_value=len(text) - substring_length))
    return (text, text[idx : idx + substring_length])  # noqa: E203


class MultipleReplaceTests(TestCase):
    @given(st.text())
    def test_no_replace(self, text: str) -> None:
        """Test that no replace array yields noop."""
        self.assertEqual(multiple_replace({}, text), text)

    @given(st.text())
    def test_empty_string_replace(self, text: str) -> None:
        """Test that no replace array yields noop."""
        with self.assertRaises(ValueError):
            multiple_replace({"": "spam"}, text)

    @given(draw_text_and_substring(5), st.text())
    @example(("I like tea", "tea"), "coffee")  # --> I like coffee
    def test_replace_single_as_replace(
        self, text_and_before: tuple, after: str
    ) -> None:
        """Test that single replacement works as str.replace."""
        text, before = text_and_before
        new_text = text.replace(before, after)
        event("new_text == text: " + str(new_text == text))
        target(-similar(new_text, text))

        self.assertEqual(multiple_replace({before: after}, text), new_text)

    def test_replace_multiple_interference(self) -> None:
        """Test that multiple replacement does not necessarily work as str.replace.

        I.e. chained invokations of str.replace may replace something that was
        already replaced. Creating undesirable cycles.
        """
        text = "I love eating"
        changes = [("I", "love"), ("love", "eating"), ("eating", "spam")]

        new_text = reduce(lambda text, change: text.replace(*change), changes, text)
        self.assertEqual(new_text, "spam spam spam")

        text = multiple_replace(dict(changes), text)
        self.assertEqual(text, "love eating spam")

    @given(st.text(), st.dictionaries(st.text(min_size=1), st.text()))
    @example(text="1", changes={"0": "2", "1": "00"})
    def test_replace_multiple_as_replace(
        self, text: str, changes: dict[str, str]
    ) -> None:
        """Test that multiple replacement works as str.replace.

        This only applies when interference does not come into play.
        """
        # Protect against interference (unlikely to occur)
        for value in changes.values():
            for key in changes.keys():
                assume(value not in key)
                assume(key not in value)

        new_text = reduce(
            lambda text, change: text.replace(*change), changes.items(), text
        )
        event("new_text == text: " + str(new_text == text))

        self.assertEqual(multiple_replace(changes, text), new_text)
