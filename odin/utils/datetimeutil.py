import re

from datetime import tzinfo, date, time, datetime, timedelta
from email.utils import formatdate as format_http_datetime  # noqa
from email.utils import parsedate_tz
from time import timezone, altzone, daylight, mktime, localtime, tzname
from typing import Dict, Any


class IgnoreTimezone:
    pass


ZERO = timedelta(0)
LOCAL_STD_OFFSET = timedelta(seconds=-timezone)
LOCAL_DST_OFFSET = timedelta(seconds=-altzone) if daylight else LOCAL_STD_OFFSET
LOCAL_DST_DIFF = LOCAL_DST_OFFSET - LOCAL_STD_OFFSET


class UTC(tzinfo):
    """
    UTC timezone.
    """
    def utcoffset(self, _) -> timedelta:
        return ZERO

    def dst(self, _) -> timedelta:
        return ZERO

    def tzname(self, _) -> str:
        return "UTC"

    def __str__(self) -> str:
        return "UTC"

    def __repr__(self) -> str:
        return "<UTC>"


utc = UTC()


def _is_dst(dt: datetime) -> bool:
    stamp = mktime((dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.weekday(), 0, 0))
    tt = localtime(stamp)
    return tt.tm_isdst > 0


class LocalTimezone(tzinfo):
    """
    The current local timezone (based on platform configuration)
    """
    def utcoffset(self, dt) -> timedelta:
        return LOCAL_DST_OFFSET if _is_dst(dt) else LOCAL_STD_OFFSET

    def dst(self, dt) -> timedelta:
        return LOCAL_DST_DIFF if _is_dst(dt) else ZERO

    def tzname(self, dt) -> str:
        return tzname[_is_dst(dt)]

    def __str__(self) -> str:
        return tzname[0]

    def __repr__(self) -> str:
        return "<LocalTimezone: {}>".format(self)


local = LocalTimezone()


class FixedTimezone(tzinfo):
    """
    A fixed timezone for when a timezone is specified by a numerical offset
    and no dst information is available.
    """
    __slots__ = ('offset', 'name',)

    @classmethod
    def from_seconds(cls, seconds: int) -> tzinfo:
        sign = '-' if seconds < 0 else ''
        minutes = abs(seconds // 60)
        hours = minutes // 60
        minutes %= 60
        name = "{}{:02d}:{:02d}".format(sign, hours, minutes)

        if sign == '-':
            hours *= -1
            minutes *= -1

        return cls(timedelta(hours=hours, minutes=minutes), name)

    @classmethod
    def from_hours_minutes(cls, hours: int, minutes: int=0) -> tzinfo:
        sign = '-' if hours < 0 else ''
        hours = abs(hours)
        minutes = abs(minutes)
        name = "{}{:02d}:{:02d}".format(sign, hours, minutes)

        if sign == '-':
            hours *= -1
            minutes *= -1

        return cls(timedelta(hours=hours, minutes=minutes), name)

    @classmethod
    def from_groups(cls, groups, default_timezone: tzinfo=utc) -> tzinfo:
        tz = groups['timezone']
        if tz is None:
            return default_timezone

        if tz in ('Z', 'GMT', 'UTC'):
            return utc

        sign = groups['tz_sign']
        hours = int(groups['tz_hour'])
        minutes = int(groups['tz_minute'] or 0)
        name = "{}{:02d}:{:02d}".format(sign, hours, minutes)

        if sign == '-':
            hours = -hours
            minutes = -minutes

        return cls(timedelta(hours=hours, minutes=minutes), name)

    def __init__(self, offset: timedelta=None, name=None) -> None:
        super().__init__()
        self.offset = offset or ZERO
        self.name = name or ''

    def utcoffset(self, _) -> timedelta:
        return self.offset

    def dst(self, _) -> timedelta:
        return ZERO

    def tzname(self, _) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name

    def __repr__(self):
        return "<FixedTimezone {!r} {!r}>".format(self.name, self.offset)

    def __eq__(self, other: 'FixedTimezone') -> bool:
        return self.offset == other.offset

    # Pickle support

    def __getstate__(self) -> Dict[str, Any]:
        return {'offset': self.offset, 'name': self.name}

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.offset = state.get('offset')
        self.name = state.get('name')


def get_tz_aware_dt(dt: datetime, assumed_tz: tzinfo=local) -> datetime:
    """
    Get a time zone aware date time from a supplied date time.

    If dt is already timezone aware it will be returned unchanged.
    If dt is not aware it will be assumed that dt is in local time.
    """
    return dt if dt.tzinfo else dt.replace(tzinfo=assumed_tz)


def utc_now() -> datetime:
    """
    Get now in UTC (with timezone set correctly).
    """
    return datetime.now(tz=utc)


now_utc = utc_now


def local_now() -> datetime:
    """
    Get now in the current local timezone.
    """
    return datetime.now(tz=local)


now_local = local_now


ISO8601_TIME_STRING_RE = re.compile(
    r"^(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(\.(?P<microseconds>\d+))?"
    r"(?P<timezone>Z|((?P<tz_sign>[-+])(?P<tz_hour>\d{2})(:(?P<tz_minute>\d{2}))?))?$")

ISO8601_DATETIME_STRING_RE = re.compile(
    r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})[tT\s]"
    r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(\.(?P<microseconds>\d+))? ?"
    r"(?P<timezone>Z|GMT|UTC|((?P<tz_sign>[-+])(?P<tz_hour>\d{2})(:?(?P<tz_minute>\d{2}))?))?$")


def parse_iso_date(date_string: str) -> date:
    """
    Parse a date in the string format defined in ISO 8601.
    """
    if not isinstance(date_string, str):
        raise ValueError("Expected string")

    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Expected ISO 8601 formatted date string.")


def parse_iso_time(time_string: str, default_timezone: tzinfo=utc) -> time:
    """
    Parse a time in the string format defined by ISO 8601.
    """
    if not isinstance(time_string, str):
        raise ValueError("Expected string")

    matches = ISO8601_TIME_STRING_RE.match(time_string)
    if not matches:
        raise ValueError("Expected ISO 8601 formatted time string.")

    groups = matches.groupdict()
    if default_timezone is IgnoreTimezone:
        tz = None
    else:
        tz = FixedTimezone.from_groups(groups, default_timezone)
    return time(
        int(groups['hour']),
        int(groups['minute']),
        int(groups['second']),
        int(groups['microseconds'] or 0),
        tz
    )


def parse_iso_datetime(datetime_string: str, default_timezone: tzinfo=utc) -> datetime:
    """
    Parse a datetime in the string format defined by ISO 8601.
    """
    if not isinstance(datetime_string, str):
        raise ValueError("Expected string")

    matches = ISO8601_DATETIME_STRING_RE.match(datetime_string)
    if not matches:
        raise ValueError("Expected ISO 8601 formatted datetime string.")

    groups = matches.groupdict()
    if default_timezone is IgnoreTimezone:
        tz = None
    else:
        tz = FixedTimezone.from_groups(groups, default_timezone)
    return datetime(
        int(groups['year']),
        int(groups['month']),
        int(groups['day']),
        int(groups['hour']),
        int(groups['minute']),
        int(groups['second']),
        int(groups['microseconds'] or 0),
        tz
    )


def to_ecma_datetime(dt: datetime, default_timezone: tzinfo=local) -> str:
    """
    Convert a python datetime into the string format defined by ECMA-262.

    See ECMA international standard: ECMA-262 section 15.9.1.15

    ``assume_local_time`` if true will assume the date time is in local time if the object is a naive date time object;
        else assumes the time value is utc.
    """
    dt = get_tz_aware_dt(dt, default_timezone).astimezone(utc)
    return "%4i-%02i-%02iT%02i:%02i:%02i.%03iZ" % (
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond / 1000)


def parse_http_datetime(datetime_string: str) -> datetime:
    """
    Parse a datetime in the string format defined by ISO-1123 (or HTTP date time).
    """
    elements = None
    if isinstance(datetime_string, str):
        elements = parsedate_tz(datetime_string)

    if not elements:
        raise ValueError("Expected ISO-1123 formatted datetime string.")

    return datetime(*elements[:6], tzinfo=FixedTimezone.from_seconds(elements[-1]))


def to_http_datetime(dt: datetime, default_timezone: tzinfo=local) -> str:
    """
    Convert a python datetime into the string format defined by ISO-1123 (or HTTP date time).
    """
    dt = get_tz_aware_dt(dt, default_timezone).astimezone(utc)
    timeval = mktime(dt.timetuple())
    now = localtime(timeval)
    return '{0}, {1:02d} {2} {3:04d} {4:02d}:{5:02d}:{6:02d} {7}'.format(
        ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][now[6]],
        now[2],
        ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][now[1] - 1],
        now[0], now[3], now[4], now[5], 'GMT'
    )
