# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any

from tqdm import tqdm as _tqdm


def tqdm(iterable: Any = None, **kwargs: Any) -> _tqdm:
    """Wrap `tqdm`, ensuring that we only print progress bars in interactive sessions,
    and *not* when running from cron or other non-interactive environments.
    # See: https://tqdm.github.io/docs/tqdm/#__init__
    """
    disable: bool = kwargs.pop("disable", None)
    return _tqdm(iterable=iterable, disable=disable, **kwargs)
