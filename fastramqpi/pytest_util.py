# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any

import tenacity
from tenacity import stop_after_delay
from tenacity import wait_fixed


def retry(
    stop: Any = stop_after_delay(20),
    wait: Any = wait_fixed(2),
) -> Any:
    """Tenacity retry decorator, with defaults useful for testing.

    Args:
        stop: Stop after 10 seconds so the test doesn't run forever.
            The default duration is long since some integrations need multiple rounds
            of AMQP messages to complete, and therefore need a long time to get in a
            consistent state.
        wait: Wait two seconds between assertion attempts.

    Returns:
        Function decorated with retrying.
    """
    # reraise=True so a false assertion fails the test
    return tenacity.retry(stop=stop, wait=wait, reraise=True)
