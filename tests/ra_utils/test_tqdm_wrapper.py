# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import MagicMock
from unittest.mock import patch

from ra_utils.tqdm_wrapper import tqdm as wrapped_tqdm


@patch("ra_utils.tqdm_wrapper._tqdm")
def test_wrapper_sets_disable_to_none(mock_tqdm: MagicMock):
    wrapped_tqdm()
    mock_tqdm.assert_called_once_with(iterable=None, disable=None)


@patch("ra_utils.tqdm_wrapper._tqdm")
def test_wrapper_respects_explicit_disable_kwarg(mock_tqdm: MagicMock):
    wrapped_tqdm(disable=True)
    mock_tqdm.assert_called_once_with(iterable=None, disable=True)


@patch("ra_utils.tqdm_wrapper._tqdm")
def test_wrapper_passes_other_kwargs(mock_tqdm: MagicMock):
    wrapped_tqdm(foo="bar")
    mock_tqdm.assert_called_once_with(iterable=None, disable=None, foo="bar")
