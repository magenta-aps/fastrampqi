# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from frozendict import frozendict

from ra_utils.transpose_dict import transpose_dict


@pytest.mark.parametrize(
    "before,after",
    [
        ({"test_key1": "test_value1"}, {"test_value1": ["test_key1"]}),
        (
            {
                "test_key1": "test_value1",
                "test_key2": "test_value2",
                "test_key3": "test_value1",
            },
            {"test_value1": ["test_key1", "test_key3"], "test_value2": ["test_key2"]},
        ),
        ({"a": {"b": "c"}}, {frozendict(b="c"): ["a"]}),
        ({"a": frozendict(b="c")}, {frozendict(b="c"): ["a"]}),
        ({"a": {"b", "c"}}, {frozenset({"b", "c"}): ["a"]}),
        ({"a": frozenset({"b": "c"})}, {frozenset({"b": "c"}): ["a"]}),
        ({"a": ["b", "c"]}, {("b", "c"): ["a"]}),
        ({"a": ("b", "c")}, {("b", "c"): ["a"]}),
        # TODO: Use other unhashables, i.e. hypothesis non_hashable_strategies
    ],
)
def test_transpose_dict(before, after):
    assert transpose_dict(before) == after
