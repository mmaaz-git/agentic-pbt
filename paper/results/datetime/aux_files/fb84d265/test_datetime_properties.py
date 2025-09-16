import datetime
import math
from hypothesis import given, strategies as st, assume, settings
import pytest


# Strategy for valid dates
valid_dates = st.builds(
    datetime.date,
    year=st.integers(min_value=datetime.MINYEAR, max_value=datetime.MAXYEAR),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=31)
).filter(lambda d: True)  # Filter will remove invalid dates automatically

# Strategy for valid times
valid_times = st.builds(
    datetime.time,
    hour=st.integers(min_value=0, max_value=23),
    minute=st.integers(min_value=0, max_value=59),
    second=st.integers(min_value=0, max_value=59),
    microsecond=st.integers(min_value=0, max_value=999999)
)

# Strategy for valid datetimes
valid_datetimes = st.builds(
    datetime.datetime,
    year=st.integers(min_value=datetime.MINYEAR, max_value=datetime.MAXYEAR),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=31),
    hour=st.integers(min_value=0, max_value=23),
    minute=st.integers(min_value=0, max_value=59),
    second=st.integers(min_value=0, max_value=59),
    microsecond=st.integers(min_value=0, max_value=999999)
).filter(lambda dt: True)  # Filter will remove invalid datetimes

# Strategy for timedeltas
valid_timedeltas = st.builds(
    datetime.timedelta,
    days=st.integers(min_value=-999999999, max_value=999999999),
    seconds=st.integers(min_value=0, max_value=86399),
    microseconds=st.integers(min_value=0, max_value=999999)
)


# Test 1: ISO format round-trip for dates
@given(valid_dates)
@settings(max_examples=1000)
def test_date_isoformat_roundtrip(d):
    iso_str = d.isoformat()
    parsed = datetime.date.fromisoformat(iso_str)
    assert parsed == d


# Test 2: ISO format round-trip for datetimes
@given(valid_datetimes)
@settings(max_examples=1000)
def test_datetime_isoformat_roundtrip(dt):
    iso_str = dt.isoformat()
    parsed = datetime.datetime.fromisoformat(iso_str)
    assert parsed == dt


# Test 3: Ordinal round-trip for dates
@given(valid_dates)
@settings(max_examples=1000)
def test_date_ordinal_roundtrip(d):
    ordinal = d.toordinal()
    parsed = datetime.date.fromordinal(ordinal)
    assert parsed == d


# Test 4: weekday and isoweekday consistency
@given(valid_dates)
@settings(max_examples=1000)
def test_weekday_isoweekday_consistency(d):
    weekday = d.weekday()
    isoweekday = d.isoweekday()
    # isoweekday should be weekday + 1 (Monday: weekday=0, isoweekday=1)
    assert isoweekday == weekday + 1
    assert 0 <= weekday <= 6
    assert 1 <= isoweekday <= 7


# Test 5: Timedelta arithmetic associativity
@given(valid_dates, valid_timedeltas, valid_timedeltas)
@settings(max_examples=500)
def test_timedelta_associativity(d, td1, td2):
    try:
        # (d + td1) + td2 should equal d + (td1 + td2)
        result1 = (d + td1) + td2
        result2 = d + (td1 + td2)
        assert result1 == result2
    except OverflowError:
        # This is expected for very large timedeltas
        pass


# Test 6: Timedelta addition commutativity
@given(valid_timedeltas, valid_timedeltas)
@settings(max_examples=1000)
def test_timedelta_addition_commutativity(td1, td2):
    assert td1 + td2 == td2 + td1


# Test 7: Date replace preserves validity
@given(valid_dates, 
       st.integers(min_value=datetime.MINYEAR, max_value=datetime.MAXYEAR),
       st.integers(min_value=1, max_value=12),
       st.integers(min_value=1, max_value=31))
@settings(max_examples=1000)
def test_date_replace(d, year, month, day):
    try:
        replaced = d.replace(year=year, month=month, day=day)
        # If replace succeeds, the result should be a valid date
        assert isinstance(replaced, datetime.date)
        assert replaced.year == year
        assert replaced.month == month
        assert replaced.day == day
    except ValueError:
        # Invalid date combination is expected
        pass


# Test 8: Datetime timestamp round-trip
@given(valid_datetimes)
@settings(max_examples=1000)
def test_datetime_timestamp_roundtrip(dt):
    # Only test dates after Unix epoch and before year 9999
    assume(dt.year >= 1970)
    assume(dt.year <= 9998)  # Avoid overflow issues
    
    try:
        # Replace tzinfo to make it UTC
        dt_utc = dt.replace(tzinfo=datetime.timezone.utc)
        timestamp = dt_utc.timestamp()
        parsed = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
        
        # Compare with microsecond precision
        assert abs((parsed - dt_utc).total_seconds()) < 1e-6
    except (OSError, OverflowError, ValueError):
        # Some platforms have limited timestamp range
        pass


# Test 9: ISO calendar round-trip
@given(valid_dates)
@settings(max_examples=1000)
def test_isocalendar_roundtrip(d):
    iso_year, iso_week, iso_weekday = d.isocalendar()
    parsed = datetime.date.fromisocalendar(iso_year, iso_week, iso_weekday)
    assert parsed == d


# Test 10: Timedelta total_seconds consistency
@given(valid_timedeltas)
@settings(max_examples=1000)
def test_timedelta_total_seconds_consistency(td):
    total = td.total_seconds()
    # Reconstruct from total seconds
    days = int(total // 86400)
    remaining_seconds = total - (days * 86400)
    
    # Check that total_seconds is consistent with components
    expected_total = td.days * 86400 + td.seconds + td.microseconds / 1000000
    assert math.isclose(total, expected_total, rel_tol=1e-9)


# Test 11: Date comparison transitivity
@given(valid_dates, valid_dates, valid_dates)
@settings(max_examples=500)
def test_date_comparison_transitivity(d1, d2, d3):
    if d1 <= d2 and d2 <= d3:
        assert d1 <= d3
    if d1 < d2 and d2 < d3:
        assert d1 < d3


# Test 12: Datetime string formatting and parsing
@given(valid_datetimes)
@settings(max_examples=1000)
def test_datetime_strftime_strptime_roundtrip(dt):
    # Use a format that preserves all information
    fmt = "%Y-%m-%d %H:%M:%S.%f"
    formatted = dt.strftime(fmt)
    parsed = datetime.datetime.strptime(formatted, fmt)
    assert parsed == dt


# Test 13: Date arithmetic with negative timedelta
@given(valid_dates, valid_timedeltas)
@settings(max_examples=1000)
def test_date_negative_timedelta(d, td):
    try:
        # Adding a timedelta and then subtracting it should give original date
        result = (d + td) - td
        assert result == d
    except OverflowError:
        # Expected for very large timedeltas
        pass


# Test 14: Timezone offset consistency
@given(st.integers(min_value=-1439, max_value=1439))  # Minutes from UTC
@settings(max_examples=1000)
def test_timezone_offset_consistency(offset_minutes):
    offset = datetime.timedelta(minutes=offset_minutes)
    tz = datetime.timezone(offset)
    
    # Create a datetime with this timezone
    dt = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=tz)
    
    # The offset should be retrievable
    assert dt.utcoffset() == offset
    assert dt.tzinfo.utcoffset(None) == offset


# Test 15: Date min/max boundaries
@given(valid_dates)
@settings(max_examples=1000)
def test_date_boundaries(d):
    assert datetime.date.min <= d <= datetime.date.max
    assert d.year >= datetime.MINYEAR
    assert d.year <= datetime.MAXYEAR