# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections.abc import Callable
from functools import partial
from typing import Dict

import pytest
from hypothesis import assume
from hypothesis import given
from hypothesis import strategies as st

from fastramqpi.ra_utils.dict_map import dict_map
from fastramqpi.ra_utils.dict_map import dict_map_key
from fastramqpi.ra_utils.dict_map import dict_map_value


def swapcase(x: str) -> str:
    return x.swapcase()


def pow2(x: int) -> int:
    return x**2


@pytest.mark.parametrize(
    "dict_map_func",
    [
        dict_map,
        partial(dict_map, key_func=swapcase),
        partial(dict_map, value_func=swapcase),
        partial(dict_map, key_func=swapcase, value_func=swapcase),
    ],
)
def test_dictmap_emptydict(dict_map_func: Callable) -> None:
    dicty: Dict[str, str] = {}
    mapped = dict_map_func(dicty)
    assert id(mapped) == id(dicty)
    assert dicty == {}


@given(st.dictionaries(st.text(), st.text(), min_size=1))
def test_dictmap_identity(dicty: dict) -> None:
    mapped = dict_map(dicty)
    assert id(mapped) == id(dicty)
    assert dict_map(mapped) == dicty


@given(st.dictionaries(st.text(), st.text(), min_size=1))
def test_dictmap_swapcase_key(dicty: dict) -> None:
    mapped = dict_map(dicty, key_func=swapcase)
    assert id(mapped) != id(dicty)
    assert sorted(mapped.keys()) == sorted(map(swapcase, dicty.keys()))
    assert sorted(mapped.values()) == sorted(dicty.values())

    key_mapped = dict_map_key(swapcase, dicty)
    assert key_mapped == mapped


@given(st.dictionaries(st.text(), st.text(), min_size=1))
def test_dictmap_swapcase_value(dicty: dict) -> None:
    mapped = dict_map(dicty, value_func=swapcase)
    assert id(mapped) != id(dicty)
    assert sorted(mapped.keys()) == sorted(dicty.keys())
    assert sorted(mapped.values()) == sorted(map(swapcase, dicty.values()))

    value_mapped = dict_map_value(swapcase, dicty)
    assert value_mapped == mapped


@given(st.dictionaries(st.text(), st.text(), min_size=1))
def test_dictmap_swapcase_key_value(dicty: dict) -> None:
    mapped = dict_map(dicty, key_func=swapcase, value_func=swapcase)
    assert id(mapped) != id(dicty)
    assert sorted(mapped.keys()) == sorted(map(swapcase, dicty.keys()))
    assert sorted(mapped.values()) == sorted(map(swapcase, dicty.values()))


@given(st.dictionaries(st.text(), st.integers(), min_size=1))
def test_dictmap_pow2_key_value(dicty: dict) -> None:
    mapped = dict_map(dicty, key_func=swapcase, value_func=pow2)
    assert id(mapped) != id(dicty)
    assert sorted(mapped.keys()) == sorted(map(swapcase, dicty.keys()))
    assert sorted(mapped.values()) == sorted(map(pow2, dicty.values()))


@given(st.dictionaries(st.text(), st.text(), min_size=1))
def test_dictmap_invalid_operation(dicty: dict) -> None:
    pow2_error = "unsupported operand type(s) for ** or pow()"

    with pytest.raises(TypeError) as exc_info:
        dict_map(dicty, key_func=pow2)
    assert pow2_error in str(exc_info.value)

    with pytest.raises(TypeError) as exc_info:
        dict_map_key(pow2, dicty)
    assert pow2_error in str(exc_info.value)

    with pytest.raises(TypeError) as exc_info:
        dict_map_value(pow2, dicty)
    assert pow2_error in str(exc_info.value)


@given(st.text(min_size=1))
def test_dict_map_destructive_key_interference(key: str) -> None:
    # Any non-bijective function would work here
    def to_upper(x: str) -> str:
        return x.upper()

    assume(key != to_upper(key))
    dicty = {key: 0, to_upper(key): 1}

    with pytest.raises(ValueError) as exc_info:
        dict_map(dicty, key_func=to_upper)
    assert "Provided `key_func` is non-bijective" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        dict_map_key(to_upper, dicty)
    assert "Provided `key_func` is non-bijective" in str(exc_info.value)
