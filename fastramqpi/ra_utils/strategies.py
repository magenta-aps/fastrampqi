# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# flake8: noqa
import re
from functools import lru_cache
from typing import Pattern

# Strategies

try:
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover
    raise ImportError("hypothesis not found - strategies not imported")


def not_from_regex(str_pat: str) -> st.SearchStrategy:
    """Generates strings that do not match the `str_pat` regex pattern.

    Inverted <a href="https://hypothesis.readthedocs.io/en/latest/data.html#hypothesis.strategies.from_regex">`hypothesis.strategies.from_regex`</a> search strategy.

    *Note: The `str_pat` regex pattern is compiled and cached internally.*

    Args:
        str_pat: The regex pattern to generate strings that does not match.

    Returns:
        Strategy that generates strings that does not match the `str_pat` regex pattern.
    """

    @lru_cache
    def cached_regex(str_pat: str) -> Pattern:
        return re.compile(str_pat)

    regex = cached_regex(str_pat)
    return st.text().filter(lambda s: regex.match(s) is None)
