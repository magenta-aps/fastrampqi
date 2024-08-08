# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic.datetime_parse import parse_datetime
from pydantic.datetime_parse import StrBytesIntFloat


MO_TZ = ZoneInfo("Europe/Copenhagen")


def parse_graphql_datetime(value: StrBytesIntFloat | datetime) -> datetime:
    """Parse OS2mo GraphQL datetime to Python object.

    Even though ISO 8601 promises "unique and unambiguous" representations of
    datetimes, it is impossible to unambiguously represent timestamp in a
    specific time zone using only a UTC offset.

    For example, the 31st October 2010 at 00:00 in Copenhagen and Cairo is both
    represented as the timestamp `2010-10-31T00:00:00+02:00`. However, one day
    later in Copenhagen is represented as `2010-11-01T00:00:00+01:00` -- now
    with a UTC offset of 01:00 because of daylight saving time -- whereas the
    timestamp in Cairo is `2010-11-01T00:00:00+02:00`.

    ISO 8601 is thus inherently a broken standard. Until RFC 9557 introduces
    proper timestamps with time zone locations, the best we can do is assume
    that everyone observes Copenhagen time.
    """
    # Datetime objects can have proper time zone information, so we refrain
    # from modifying it. Values received from OS2mo will always be strings.
    if isinstance(value, datetime):
        return value
    dt = parse_datetime(value)
    # Only assume Copenhagen time if UTC offset matches Copenhagen
    if dt.utcoffset() != dt.astimezone(MO_TZ).utcoffset():
        return dt
    return dt.replace(tzinfo=MO_TZ)
