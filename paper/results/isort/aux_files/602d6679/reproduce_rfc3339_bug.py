#!/usr/bin/env python3
"""Reproduce the RFC3339 microsecond parsing bug."""

import datetime
import math
import re


class TimezoneInfo(datetime.tzinfo):
    def __init__(self, h, m):
        self._name = "UTC"
        if h != 0 and m != 0:
            self._name += "%+03d:%2d" % (h, m)
        self._delta = datetime.timedelta(hours=h, minutes=math.copysign(m, h))

    def utcoffset(self, dt):
        return self._delta

    def tzname(self, dt):
        return self._name

    def dst(self, dt):
        return datetime.timedelta(0)


UTC = TimezoneInfo(0, 0)

_re_rfc3339 = re.compile(
    r"(\d\d\d\d)-(\d\d)-(\d\d)"  # full-date
    r"[ Tt]"  # Separator
    r"(\d\d):(\d\d):(\d\d)([.,]\d+)?"  # partial-time
    r"([zZ ]|[-+]\d\d?:\d\d)?",  # time-offset
    re.VERBOSE + re.IGNORECASE,
)
_re_timezone = re.compile(r"([-+])(\d\d?):?(\d\d)?")


def parse_rfc3339(s):
    if isinstance(s, datetime.datetime):
        if not s.tzinfo:
            return s.replace(tzinfo=UTC)
        return s
    groups = _re_rfc3339.search(s).groups()
    dt = [0] * 7
    for x in range(6):
        dt[x] = int(groups[x])
    if groups[6] is not None:
        dt[6] = int(groups[6])  # BUG: This line causes the error
    tz = UTC
    if groups[7] is not None and groups[7] != 'Z' and groups[7] != 'z':
        tz_groups = _re_timezone.search(groups[7]).groups()
        hour = int(tz_groups[1])
        minute = 0
        if tz_groups[0] == "-":
            hour *= -1
        if tz_groups[2]:
            minute = int(tz_groups[2])
        tz = TimezoneInfo(hour, minute)
    return datetime.datetime(
        year=dt[0], month=dt[1], day=dt[2], hour=dt[3], minute=dt[4], second=dt[5], microsecond=dt[6], tzinfo=tz
    )


# Demonstrate the bug
print("Demonstrating RFC3339 microsecond parsing bug:\n")

# Valid RFC3339 timestamps with fractional seconds
test_cases = [
    "2024-01-01T12:00:00.1Z",       # 0.1 seconds
    "2024-01-01T12:00:00.123Z",     # 0.123 seconds
    "2024-01-01T12:00:00.123456Z",  # 0.123456 seconds
    "2024-01-01T12:00:00,123Z",     # Comma separator (valid per RFC3339)
]

for date_str in test_cases:
    print(f"Parsing: {date_str}")
    try:
        result = parse_rfc3339(date_str)
        print(f"  ✓ Success: {result}")
        print(f"    Microseconds: {result.microsecond}")
    except ValueError as e:
        print(f"  ✗ CRASH: {e}")
    print()

print("\nAnalysis:")
print("The regex captures fractional seconds including the decimal point")
print("(e.g., '.123' or ',123'), but the code tries to convert this")
print("directly to an integer with int(groups[6]), which fails.")
print("\nThe fractional part needs to be processed differently:")
print("1. Remove the leading '.' or ','")
print("2. Pad or truncate to 6 digits for microseconds")
print("3. Then convert to integer")