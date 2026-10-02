# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest

from fastramqpi.os2mo_dar_client.dar_client import _status


@pytest.mark.parametrize(
    "status,expected",
    [
        # Lookups return the status as a string, Adressevask as an integer
        ("2", {"status": 3, "darstatus": 2}),
        ("3", {"status": 1, "darstatus": 3}),
        ("4", {"status": 2, "darstatus": 4}),
        ("5", {"status": 4, "darstatus": 5}),
        (3, {"status": 1, "darstatus": 3}),
        # DAR codes without a DAWA equivalent
        ("1", {"status": None, "darstatus": 1}),
        ("6", {"status": None, "darstatus": 6}),
        # Missing status
        (None, {"status": None, "darstatus": None}),
    ],
)
def test_status(status: str | int | None, expected: dict[str, int | None]) -> None:
    """Test conversion of DAR status codes to DAWA's status fields."""
    assert _status(status) == expected
