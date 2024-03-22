# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio
from typing import Type

import pytest

from fastramqpi.ra_utils.asyncio_utils import gather_with_concurrency


@pytest.mark.parametrize(
    "parallel, exception",
    [
        (-1, ValueError),
        ("1", TypeError),
    ],
)
async def test_gather_with_concurrency_invalid_input(
    parallel: int, exception: Type
) -> None:
    """Test that invalid inputs are rejected.

    Args:
        parallel: Number of tasks to run in parallel.

    Returns:
        None
    """

    async def task(i: int) -> int:
        """Dummy noop task.

        Args:
            i: Task id

        Returns:
            Task id
        """
        return i

    tasks = list(map(task, range(10)))

    with pytest.raises(exception):
        await gather_with_concurrency(parallel, *tasks)


@pytest.mark.parametrize(
    "parallel,num_tasks",
    [
        (1, 0),
        (100, 0),
        (1, 100),
        (1000, 5),
        (5, 1000),
    ],
)
async def test_gather_with_concurrency(parallel: int, num_tasks: int) -> None:
    """Test that gather_with_concurrency works as expected.

    That is, that only parallel number of tasks are started in parallel.

    Args:
        parallel: Number of tasks to run in parallel.
        num_tasks: Number of tasks to spawn.

    Returns:
        None
    """
    blocker = asyncio.Event()
    seen = set()
    save = set()

    async def intensive_task(i: int) -> int:
        """An emulated intensive task that we cannot run with high parallelity.

        Args:
            i: Task id

        Returns:
            Task id
        """
        seen.add(i)
        await blocker.wait()
        return i

    def unleasher() -> None:
        """Save how many tasks have been started, and release all tasks.

        Returns:
            None
        """
        save.update(seen)
        blocker.set()

    # Schedule the releaser after intensive_tasks are blocked
    loop = asyncio.get_running_loop()
    loop.call_later(0.0001, unleasher)

    # Create and fire tasks
    tasks = list(map(intensive_task, range(num_tasks)))
    result = await gather_with_concurrency(parallel, *tasks)
    assert len(save) == min(parallel, num_tasks)
    assert len(result) == num_tasks
