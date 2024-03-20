# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from itertools import chain
from typing import cast
from typing import Sequence

import hypothesis.strategies as st
from hypothesis.strategies import SearchStrategy

_has_zoneinfo = True
try:
    import zoneinfo  # noqa: F401
except ImportError:  # pragma: no cover
    _has_zoneinfo = False


def deferred_hashable() -> SearchStrategy:
    stategies: Sequence[SearchStrategy] = list(
        chain(chain(base_strategies, recursive_strategies))
    )
    return cast(SearchStrategy, st.one_of(stategies))


base_strategies: Sequence[SearchStrategy] = list(
    chain(
        [
            st.binary(),
            st.booleans(),
            st.characters(),
            st.complex_numbers(allow_nan=False),
            st.dates(),
            st.datetimes(),
            st.decimals(allow_nan=False),
            st.emails(),
            st.floats(allow_nan=False),
            st.fractions(),
            st.functions(),
            st.integers(),
            st.ip_addresses(),
            st.none(),
            st.text(),
            st.timedeltas(),
            st.times(),
            st.uuids(),
        ],
        [
            st.timezone_keys(),
            st.timezones(),
        ]
        if _has_zoneinfo
        else [],
    )
)
non_hashable_strategies: Sequence[SearchStrategy] = [
    st.slices(1),
    st.dictionaries(
        keys=st.deferred(deferred_hashable), values=st.deferred(deferred_hashable)
    ),
    st.lists(st.deferred(deferred_hashable)),
    st.sets(st.deferred(deferred_hashable)),
]
recursive_strategies: Sequence[SearchStrategy] = [
    st.frozensets(st.deferred(deferred_hashable)),
    st.iterables(st.deferred(deferred_hashable)),
    st.tuples(st.deferred(deferred_hashable)),
]
combined_strategies: Sequence[SearchStrategy] = list(
    chain(base_strategies, recursive_strategies, non_hashable_strategies)
)
any_strategy: SearchStrategy = st.one_of(combined_strategies)
