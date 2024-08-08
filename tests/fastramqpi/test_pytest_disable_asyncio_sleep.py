# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import asyncio
from typing import cast

import pytest

from fastramqpi.ra_utils.catchtime import catchtime


async def test_asyncio_sleep() -> None:
    with catchtime() as t:
        await asyncio.sleep(1)

    time_spent = cast(float, t())
    assert time_spent >= 1


@pytest.mark.usefixtures("disable_asyncio_sleep")
async def test_asyncio_sleep_disabled() -> None:
    with catchtime() as t:
        await asyncio.sleep(1)

    time_spent = cast(float, t())
    assert time_spent < 1
