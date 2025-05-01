# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from operator import attrgetter
from operator import delitem
from operator import getitem
from operator import itemgetter
from operator import setitem
from typing import Any

import hypothesis.strategies as st
from hypothesis import assume
from hypothesis import given

from fastramqpi.ra_utils.attrdict import AttrDict
from fastramqpi.ra_utils.attrdict import attrdict

from .utils import any_strategy


def check_status_key(attr_dict: AttrDict, key: str, value: Any) -> None:
    assert attr_dict[key] == value
    assert getitem(attr_dict, key) == value
    assert getattr(attr_dict, key) == value
    assert itemgetter(key)(attr_dict) == value
    assert attrgetter(key)(attr_dict) == value
    assert attr_dict.__getitem__(key) == value
    assert attr_dict.__getattr__(key) == value


def check_status(attr_dict: AttrDict, value: Any) -> None:
    check_status_key(attr_dict, "status", value)
    assert attr_dict.status == value  # type: ignore


@given(value=any_strategy)
def test_getattr_static(value: Any) -> None:
    dicty = {"status": value}
    assert dicty["status"] == value
    assert getitem(dicty, "status") == value
    assert itemgetter("status")(dicty) == value

    attr_dict = attrdict(dicty)
    check_status(attr_dict, value)


@given(value=any_strategy)
def test_setattr_static(value: Any) -> None:
    dicty = {}
    dicty["status"] = value
    assert dicty["status"] == value

    attr_dict = attrdict({})
    attr_dict["status"] = value
    check_status(attr_dict, value)

    attr_dict = attrdict({})
    setitem(attr_dict, "status", value)
    check_status(attr_dict, value)

    attr_dict = attrdict({})
    attr_dict.status = value  # type: ignore
    check_status(attr_dict, value)

    attr_dict = attrdict({})
    setattr(attr_dict, "status", value)
    check_status(attr_dict, value)


@given(value=any_strategy)
def test_delattr_static(value: Any) -> None:
    dicty = {"status": value}
    del dicty["status"]
    assert dicty == {}

    attr_dict = attrdict({"status": value})
    del attr_dict["status"]
    assert attr_dict == {}

    attr_dict = attrdict({"status": value})
    delitem(attr_dict, "status")
    assert attr_dict == {}

    attr_dict = attrdict({"status": value})
    del attr_dict.status  # type: ignore
    assert attr_dict == {}

    attr_dict = attrdict({"status": value})
    delattr(attr_dict, "status")
    assert attr_dict == {}


@given(key=st.text(min_size=1), value=any_strategy)
def test_getattr_dynamic(key: str, value: Any) -> None:
    assume("." not in key)

    dicty = {key: value}
    assert dicty[key] == value
    assert getitem(dicty, key) == value
    assert itemgetter(key)(dicty) == value

    attr_dict = attrdict(dicty)
    check_status_key(attr_dict, key, value)


@given(key=st.text(min_size=1), value=any_strategy)
def test_setattr_dynamic(key: str, value: Any) -> None:
    assume("." not in key)

    dicty = {}
    dicty[key] = value
    assert dicty[key] == value

    attr_dict = attrdict({})
    attr_dict[key] = value
    check_status_key(attr_dict, key, value)

    attr_dict = attrdict({})
    setitem(attr_dict, key, value)
    check_status_key(attr_dict, key, value)

    attr_dict = attrdict({})
    setattr(attr_dict, key, value)
    check_status_key(attr_dict, key, value)


@given(key=st.text(min_size=1), value=any_strategy)
def test_delattr_dynamic(key: str, value: Any) -> None:
    assume("." not in key)

    dicty = {key: value}
    del dicty[key]
    assert dicty == {}

    attr_dict = attrdict({key: value})
    del attr_dict[key]
    assert attr_dict == {}

    attr_dict = attrdict({key: value})
    delitem(attr_dict, key)
    assert attr_dict == {}

    attr_dict = attrdict({key: value})
    delattr(attr_dict, key)
    assert attr_dict == {}


def test_constructor() -> None:
    attr_dict1 = AttrDict({})
    attr_dict2 = attrdict({})
    assert attr_dict1 == attr_dict2
