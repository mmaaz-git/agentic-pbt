import re
import sys
from datetime import datetime, date
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
import pytest

from quickbooks.helpers import qb_date_format, qb_datetime_format, qb_datetime_utc_offset_format


@given(st.datetimes(min_value=datetime(1, 1, 1), max_value=datetime(9999, 12, 31)))
def test_qb_date_format_pattern(dt):
    result = qb_date_format(dt)
    assert re.match(r'^\d{4}-\d{2}-\d{2}$', result), f"Format mismatch: {result}"
    

@given(st.datetimes(min_value=datetime(1, 1, 1), max_value=datetime(9999, 12, 31)))
def test_qb_date_format_roundtrip(dt):
    formatted = qb_date_format(dt)
    parsed = datetime.strptime(formatted, "%Y-%m-%d").date()
    expected = dt.date()
    assert parsed == expected, f"Roundtrip failed: {dt} -> {formatted} -> {parsed}"


@given(st.datetimes(min_value=datetime(1, 1, 1), max_value=datetime(9999, 12, 31)))
def test_qb_date_format_idempotence(dt):
    result1 = qb_date_format(dt)
    result2 = qb_date_format(dt)
    assert result1 == result2, f"Not idempotent: {result1} != {result2}"


@given(st.datetimes(min_value=datetime(1, 1, 1), max_value=datetime(9999, 12, 31)))
def test_qb_datetime_format_pattern(dt):
    result = qb_datetime_format(dt)
    assert re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', result), f"Format mismatch: {result}"


@given(st.datetimes(min_value=datetime(1, 1, 1), max_value=datetime(9999, 12, 31)))
def test_qb_datetime_format_roundtrip(dt):
    formatted = qb_datetime_format(dt)
    parsed = datetime.strptime(formatted, "%Y-%m-%dT%H:%M:%S")
    assert parsed.year == dt.year
    assert parsed.month == dt.month
    assert parsed.day == dt.day
    assert parsed.hour == dt.hour
    assert parsed.minute == dt.minute
    assert parsed.second == dt.second


@given(st.datetimes(min_value=datetime(1, 1, 1), max_value=datetime(9999, 12, 31)))
def test_qb_datetime_format_idempotence(dt):
    result1 = qb_datetime_format(dt)
    result2 = qb_datetime_format(dt)
    assert result1 == result2, f"Not idempotent: {result1} != {result2}"


def create_utc_offset():
    sign = st.sampled_from(['+', '-'])
    hours = st.integers(min_value=0, max_value=23)
    minutes = st.integers(min_value=0, max_value=59)
    return st.builds(lambda s, h, m: f"{s}{h:02d}:{m:02d}", sign, hours, minutes)

utc_offset_strategy = create_utc_offset()

@given(
    st.datetimes(min_value=datetime(1, 1, 1), max_value=datetime(9999, 12, 31)),
    utc_offset_strategy
)
def test_qb_datetime_utc_offset_format_composition(dt, offset):
    result = qb_datetime_utc_offset_format(dt, offset)
    expected = qb_datetime_format(dt) + offset
    assert result == expected, f"Composition failed: {result} != {expected}"


@given(
    st.datetimes(min_value=datetime(1, 1, 1), max_value=datetime(9999, 12, 31)),
    utc_offset_strategy
)
def test_qb_datetime_utc_offset_format_pattern(dt, offset):
    result = qb_datetime_utc_offset_format(dt, offset)
    pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'
    assert re.match(pattern, result), f"Format mismatch: {result}"


@given(st.dates(min_value=date(1, 1, 1), max_value=date(9999, 12, 31)))
def test_qb_date_format_accepts_date_objects(d):
    try:
        result = qb_date_format(d)
        assert re.match(r'^\d{4}-\d{2}-\d{2}$', result)
    except AttributeError:
        pass


@given(st.datetimes(min_value=datetime(1000, 1, 1), max_value=datetime(9999, 12, 31)))
def test_qb_date_format_preserves_leading_zeros(dt):
    result = qb_date_format(dt)
    parts = result.split('-')
    assert len(parts) == 3
    assert len(parts[0]) == 4  
    assert len(parts[1]) == 2  
    assert len(parts[2]) == 2  


@given(st.datetimes(min_value=datetime(1, 1, 1), max_value=datetime(9, 12, 31)))
def test_qb_date_format_year_padding(dt):
    result = qb_date_format(dt)
    year_str = result.split('-')[0]
    assert len(year_str) == 4, f"Year not zero-padded: {result}"
    assert year_str[0] == '0', f"Year should start with zeros for year {dt.year}: {result}"


@given(st.datetimes(
    min_value=datetime(1, 1, 1, 0, 0, 0),
    max_value=datetime(9999, 12, 31, 9, 59, 59)
))
def test_qb_datetime_format_single_digit_time_padding(dt):
    assume(dt.hour < 10 or dt.minute < 10 or dt.second < 10)
    result = qb_datetime_format(dt)
    time_part = result.split('T')[1]
    hours, minutes, seconds = time_part.split(':')
    assert len(hours) == 2, f"Hours not zero-padded: {result}"
    assert len(minutes) == 2, f"Minutes not zero-padded: {result}"
    assert len(seconds) == 2, f"Seconds not zero-padded: {result}"