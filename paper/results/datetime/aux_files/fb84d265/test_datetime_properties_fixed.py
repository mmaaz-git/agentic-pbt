import datetime
import math
from hypothesis import given, strategies as st, assume, settings
import pytest


# More sophisticated strategy for valid dates
@st.composite
def valid_dates(draw):
    year = draw(st.integers(min_value=datetime.MINYEAR, max_value=datetime.MAXYEAR))
    month = draw(st.integers(min_value=1, max_value=12))
    
    # Determine max day based on month and year
    if month in [1, 3, 5, 7, 8, 10, 12]:
        max_day = 31
    elif month in [4, 6, 9, 11]:
        max_day = 30
    else:  # February
        # Check for leap year
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            max_day = 29
        else:
            max_day = 28
    
    day = draw(st.integers(min_value=1, max_value=max_day))
    return datetime.date(year, month, day)


@st.composite
def valid_datetimes(draw):
    date = draw(valid_dates())
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    microsecond = draw(st.integers(min_value=0, max_value=999999))
    return datetime.datetime(date.year, date.month, date.day, hour, minute, second, microsecond)


valid_times = st.builds(
    datetime.time,
    hour=st.integers(min_value=0, max_value=23),
    minute=st.integers(min_value=0, max_value=59),
    second=st.integers(min_value=0, max_value=59),
    microsecond=st.integers(min_value=0, max_value=999999)
)

valid_timedeltas = st.builds(
    datetime.timedelta,
    days=st.integers(min_value=-999999999, max_value=999999999),
    seconds=st.integers(min_value=0, max_value=86399),
    microseconds=st.integers(min_value=0, max_value=999999)
)


# Test 1: ISO format round-trip for dates
@given(valid_dates())
@settings(max_examples=1000)
def test_date_isoformat_roundtrip(d):
    iso_str = d.isoformat()
    parsed = datetime.date.fromisoformat(iso_str)
    assert parsed == d


# Test 2: ISO format round-trip for datetimes
@given(valid_datetimes())
@settings(max_examples=1000)
def test_datetime_isoformat_roundtrip(dt):
    iso_str = dt.isoformat()
    parsed = datetime.datetime.fromisoformat(iso_str)
    assert parsed == dt


# Test 3: Ordinal round-trip for dates
@given(valid_dates())
@settings(max_examples=1000)
def test_date_ordinal_roundtrip(d):
    ordinal = d.toordinal()
    parsed = datetime.date.fromordinal(ordinal)
    assert parsed == d


# Test 4: weekday and isoweekday consistency
@given(valid_dates())
@settings(max_examples=1000)
def test_weekday_isoweekday_consistency(d):
    weekday = d.weekday()
    isoweekday = d.isoweekday()
    assert isoweekday == weekday + 1
    assert 0 <= weekday <= 6
    assert 1 <= isoweekday <= 7


# Test 5: Timedelta arithmetic associativity
@given(valid_dates(), valid_timedeltas, valid_timedeltas)
@settings(max_examples=500)
def test_timedelta_associativity(d, td1, td2):
    try:
        result1 = (d + td1) + td2
        result2 = d + (td1 + td2)
        assert result1 == result2
    except OverflowError:
        pass


# Test 6: Timedelta addition commutativity
@given(valid_timedeltas, valid_timedeltas)
@settings(max_examples=1000)
def test_timedelta_addition_commutativity(td1, td2):
    try:
        assert td1 + td2 == td2 + td1
    except OverflowError:
        pass


# Test 7: Datetime timestamp round-trip
@given(valid_datetimes())
@settings(max_examples=1000)
def test_datetime_timestamp_roundtrip(dt):
    assume(dt.year >= 1970)
    assume(dt.year <= 3000)
    
    try:
        dt_utc = dt.replace(tzinfo=datetime.timezone.utc)
        timestamp = dt_utc.timestamp()
        parsed = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
        
        # Compare with microsecond precision
        assert abs((parsed - dt_utc).total_seconds()) < 1e-6
    except (OSError, OverflowError, ValueError):
        pass


# Test 8: ISO calendar round-trip
@given(valid_dates())
@settings(max_examples=1000)
def test_isocalendar_roundtrip(d):
    iso_year, iso_week, iso_weekday = d.isocalendar()
    parsed = datetime.date.fromisocalendar(iso_year, iso_week, iso_weekday)
    assert parsed == d


# Test 9: Timedelta total_seconds consistency
@given(valid_timedeltas)
@settings(max_examples=1000)
def test_timedelta_total_seconds_consistency(td):
    total = td.total_seconds()
    expected_total = td.days * 86400 + td.seconds + td.microseconds / 1000000
    assert math.isclose(total, expected_total, rel_tol=1e-9)


# Test 10: Date comparison transitivity
@given(valid_dates(), valid_dates(), valid_dates())
@settings(max_examples=500)
def test_date_comparison_transitivity(d1, d2, d3):
    if d1 <= d2 and d2 <= d3:
        assert d1 <= d3
    if d1 < d2 and d2 < d3:
        assert d1 < d3


# Test 11: Datetime string formatting and parsing
@given(valid_datetimes())
@settings(max_examples=1000)
def test_datetime_strftime_strptime_roundtrip(dt):
    fmt = "%Y-%m-%d %H:%M:%S.%f"
    formatted = dt.strftime(fmt)
    parsed = datetime.datetime.strptime(formatted, fmt)
    assert parsed == dt


# Test 12: Date arithmetic with negative timedelta
@given(valid_dates(), valid_timedeltas)
@settings(max_examples=1000)
def test_date_negative_timedelta(d, td):
    try:
        result = (d + td) - td
        assert result == d
    except OverflowError:
        pass


# Test 13: Timezone offset consistency
@given(st.integers(min_value=-1439, max_value=1439))
@settings(max_examples=1000)
def test_timezone_offset_consistency(offset_minutes):
    offset = datetime.timedelta(minutes=offset_minutes)
    tz = datetime.timezone(offset)
    
    dt = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=tz)
    
    assert dt.utcoffset() == offset
    assert dt.tzinfo.utcoffset(None) == offset


# Test 14: Date boundaries
@given(valid_dates())
@settings(max_examples=1000)
def test_date_boundaries(d):
    assert datetime.date.min <= d <= datetime.date.max
    assert d.year >= datetime.MINYEAR
    assert d.year <= datetime.MAXYEAR


# Test 15: Time isoformat round-trip
@given(valid_times)
@settings(max_examples=1000)
def test_time_isoformat_roundtrip(t):
    iso_str = t.isoformat()
    parsed = datetime.time.fromisoformat(iso_str)
    assert parsed == t


# Test 16: Date arithmetic overflow detection
@given(valid_dates(), st.integers(min_value=-999999999, max_value=999999999))
@settings(max_examples=1000)
def test_date_arithmetic_overflow(d, days):
    td = datetime.timedelta(days=days)
    try:
        result = d + td
        # If no overflow, result should be a valid date
        assert isinstance(result, datetime.date)
        assert datetime.MINYEAR <= result.year <= datetime.MAXYEAR
    except OverflowError:
        # Overflow is expected for very large timedeltas
        pass


# Test 17: Datetime fold behavior with timezone
@given(valid_datetimes(), st.integers(min_value=0, max_value=1))
@settings(max_examples=500)
def test_datetime_fold_property(dt, fold):
    dt_with_fold = dt.replace(fold=fold)
    assert dt_with_fold.fold == fold
    # Without timezone, fold shouldn't affect equality
    assert dt_with_fold.replace(fold=0) == dt_with_fold.replace(fold=1)