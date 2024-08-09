# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from zoneinfo import ZoneInfo

from fastramqpi.ariadne import parse_graphql_datetime


def test_parse_graphql_datetime_datetime() -> None:
    """Test that a datetime's timezone is unmodified."""
    cairo = ZoneInfo("Africa/Cairo")
    dt = datetime(2010, 10, 31, 0, 0, 0, tzinfo=cairo)
    assert parse_graphql_datetime(dt).tzinfo == cairo


def test_parse_graphql_datetime_only_copenhagen_offset() -> None:
    """Test that the function only casts Copenhagen UTC offsets to Copenhagen."""
    assert parse_graphql_datetime("2010-10-31T00:00:00+10:00").tzinfo == timezone(
        timedelta(hours=10)
    )


def test_parse_graphql_datetime_str() -> None:
    """Test that the function correctly outputs Europe/Copenhagen timezones."""
    timestamp = "2010-10-31T00:00:00+02:00"
    utc_offset = datetime.fromisoformat(timestamp)
    copenhagen = parse_graphql_datetime(timestamp)
    assert copenhagen.tzinfo == ZoneInfo("Europe/Copenhagen")
    assert copenhagen.isoformat() == utc_offset.isoformat()

    one_day = timedelta(days=1)
    assert (copenhagen + one_day).isoformat() == "2010-11-01T00:00:00+01:00"
    assert (utc_offset + one_day).isoformat() == "2010-11-01T00:00:00+02:00"
