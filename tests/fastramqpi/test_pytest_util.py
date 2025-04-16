# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import time
from typing import NoReturn

import pytest
from tenacity import stop_after_delay

from fastramqpi.pytest_util import retry


def test_retry() -> None:
    """Test the retry decorator."""

    @retry(stop=stop_after_delay(2))
    def f() -> NoReturn:
        raise ValueError()

    start_time = time.monotonic()
    with pytest.raises(ValueError):
        f()
    end_time = time.monotonic()

    assert 2 <= (end_time - start_time) <= 3
