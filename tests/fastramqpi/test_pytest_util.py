# SPDX-FileCopyrightText: Magenta ApS
# SPDX-License-Identifier: MPL-2.0
import re
import time
from typing import Callable
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


# This function is here to ensure that @retry does not ruin our function typing, i.e.
# to ensure that mypy is happy with the return-type of our function.
def retry_typing() -> Callable[[int], bool]:
    @retry()
    def is_even(x: int) -> bool:
        return bool(re.search(r"[02468]$", str(x)))

    return is_even
