# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import re
from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from fastramqpi.ra_utils.strategies import not_from_regex

# Tests


@given(st.data())
def test_not_from_regex(data: Any) -> None:
    test_str = r"^" + re.escape(data.draw(st.text())) + "$"
    not_matching = data.draw(not_from_regex(test_str))
    assert re.match(test_str, not_matching) is None
