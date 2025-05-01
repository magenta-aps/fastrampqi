# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import timedelta
from time import sleep
from typing import Tuple
from typing import cast
from unittest import TestCase

import hypothesis.strategies as st
from hypothesis import given
from hypothesis import settings

from fastramqpi.ra_utils.catchtime import catchtime


class CatchtimeTests(TestCase):
    """Test the catchtime contextmanager works as expected."""

    @settings(max_examples=15, deadline=timedelta(milliseconds=1100))
    @given(st.floats(min_value=0.2, max_value=1))
    def test_catchtime(self, sleep_time: float) -> None:
        """Test that catchtime returns the expected time."""
        with catchtime() as t:
            sleep(sleep_time)
        time_spent = cast(float, t())

        self.assertLess(time_spent - sleep_time, 0.01)

    @settings(max_examples=15, deadline=timedelta(milliseconds=1100))
    @given(st.floats(min_value=0.2, max_value=1))
    def test_catchtime_process(self, sleep_time: float) -> None:
        """Test that catchtime returns the expected time and process time."""
        with catchtime(include_process_time=True) as t:
            sleep(sleep_time)
        time_spent, process_time = cast(Tuple[float, float], t())

        self.assertLess(time_spent - sleep_time, 0.01)
        self.assertLess(process_time, time_spent - sleep_time)
