import datetime
from hypothesis import given, strategies as st, assume, settings, note
from dateutil import parser, rrule, tz
import pytest


# Test parser round-trip with timezone info
@st.composite
def datetime_with_tz(draw):
    """Generate datetime objects with various timezones"""
    dt = draw(st.datetimes(
        min_value=datetime.datetime(1900, 1, 1),
        max_value=datetime.datetime(2100, 12, 31)
    ))
    
    # Add timezone
    tz_choice = draw(st.integers(min_value=0, max_value=3))
    if tz_choice == 0:
        # UTC
        dt = dt.replace(tzinfo=tz.UTC)
    elif tz_choice == 1:
        # Fixed offset
        hours = draw(st.integers(min_value=-12, max_value=14))
        dt = dt.replace(tzinfo=tz.tzoffset(None, hours * 3600))
    
    return dt


@given(datetime_with_tz())
def test_parser_str_roundtrip(dt):
    """Test that parsing string representation works"""
    dt_str = str(dt)
    try:
        parsed = parser.parse(dt_str)
        # Check components match (may lose microsecond precision in string)
        assert parsed.year == dt.year
        assert parsed.month == dt.month
        assert parsed.day == dt.day
        assert parsed.hour == dt.hour
        assert parsed.minute == dt.minute
        assert parsed.second == dt.second
    except parser.ParserError:
        pass


# Test rrule weekly recurrence edge cases  
@given(
    st.integers(min_value=0, max_value=6),  # weekday
    st.integers(min_value=1, max_value=52),  # weeks
    st.integers(min_value=1, max_value=10)   # count
)
def test_rrule_weekly_consistency(weekday, interval, count):
    """Test weekly rrule produces consistent spacing"""
    start = datetime.datetime(2020, 1, 6)  # A Monday
    
    # Adjust start to the desired weekday
    days_ahead = (weekday - start.weekday()) % 7
    start = start + datetime.timedelta(days=days_ahead)
    
    rule = rrule.rrule(
        rrule.WEEKLY,
        count=count,
        interval=interval,
        dtstart=start
    )
    
    occurrences = list(rule)
    
    # Check all occurrences are on the same weekday
    for occ in occurrences:
        assert occ.weekday() == weekday
    
    # Check spacing is exactly 'interval' weeks
    for i in range(1, len(occurrences)):
        delta = occurrences[i] - occurrences[i-1]
        assert delta.days == interval * 7


# Test rrule with UNTIL and COUNT should not both be set
def test_rrule_until_count_exclusive():
    """Test that rrule doesn't accept both UNTIL and COUNT"""
    start = datetime.datetime(2020, 1, 1)
    until = datetime.datetime(2020, 12, 31)
    
    # This should raise an error or ignore one parameter
    try:
        rule = rrule.rrule(
            rrule.DAILY,
            count=10,
            until=until,
            dtstart=start
        )
        # If it doesn't raise, check which parameter wins
        occurrences = list(rule)
        # Either count or until should be respected, not both
        assert len(occurrences) == 10 or occurrences[-1] <= until
    except ValueError:
        # This is acceptable - rejecting both parameters
        pass


# Test parser with ambiguous dates
@given(st.integers(min_value=1, max_value=12))
def test_parser_ambiguous_date_consistency(num):
    """Test parser consistency with ambiguous dates like 01/02/03"""
    # Could be Jan 2, 2003 or Feb 1, 2003 or other interpretations
    date_str = f"{num:02d}/03/04"
    
    # Parse with dayfirst
    result_dayfirst = parser.parse(date_str, dayfirst=True)
    # Parse with dayfirst=False (default)
    result_monthfirst = parser.parse(date_str, dayfirst=False)
    
    # They should give different results for ambiguous dates
    if num <= 12 and num != 3:
        # Both are valid but different interpretations
        if num < 3 or num > 3:
            assert result_dayfirst != result_monthfirst


# Test parser default date behavior
@given(st.text(min_size=1, max_size=20, alphabet="0123456789:"))
def test_parser_default_date(time_str):
    """Test parser with partial date/time strings uses today's date"""
    try:
        # Try parsing as time only
        default = datetime.datetime(2020, 6, 15, 0, 0, 0)
        result = parser.parse(time_str, default=default)
        
        # If it parses successfully, verify default was used appropriately
        if ":" in time_str and not any(c in time_str for c in ["/"]):
            # Likely just a time - should use default date
            assert result.year == 2020
            assert result.month == 6
            assert result.day == 15
    except (parser.ParserError, ValueError, OverflowError):
        pass


# Test timezone conversion round-trip
@given(st.integers(min_value=-12, max_value=14))
def test_tz_offset_arithmetic(hours):
    """Test timezone offset arithmetic"""
    offset = tz.tzoffset("TEST", hours * 3600)
    
    # Create a datetime with this timezone
    dt = datetime.datetime(2020, 6, 15, 12, 0, 0, tzinfo=offset)
    
    # Convert to UTC and back
    dt_utc = dt.astimezone(tz.UTC)
    dt_back = dt_utc.astimezone(offset)
    
    assert dt == dt_back
    assert dt.hour == dt_back.hour
    assert dt.tzinfo.utcoffset(dt) == dt_back.tzinfo.utcoffset(dt_back)


# Test rrule string parsing round-trip
def test_rrule_str_roundtrip():
    """Test rrule to string and back"""
    rule = rrule.rrule(
        rrule.WEEKLY,
        count=5,
        byweekday=(rrule.MO, rrule.WE, rrule.FR),
        dtstart=datetime.datetime(2020, 1, 1)
    )
    
    # Get string representation
    rule_str = str(rule)
    
    # This should contain the RRULE RFC format
    assert "RRULE" in rule_str or "DTSTART" in rule_str


# Test for parser timezone handling
@given(st.integers(min_value=-12, max_value=14))
def test_parser_timezone_offset_parsing(offset_hours):
    """Test parser handles timezone offsets correctly"""
    
    # Create ISO string with timezone
    if offset_hours >= 0:
        tz_str = f"+{offset_hours:02d}:00"
    else:
        tz_str = f"{offset_hours:03d}:00"
    
    dt_str = f"2020-06-15T12:00:00{tz_str}"
    
    parsed = parser.isoparse(dt_str)
    
    # Check timezone was parsed correctly
    assert parsed.tzinfo is not None
    offset = parsed.tzinfo.utcoffset(parsed)
    expected_offset = datetime.timedelta(hours=offset_hours)
    assert offset == expected_offset


# Test recurrence rule boundary conditions
@given(st.integers(min_value=1, max_value=31))
def test_rrule_monthly_bymonthday(day):
    """Test monthly recurrence by month day"""
    start = datetime.datetime(2020, 1, 1)
    
    try:
        rule = rrule.rrule(
            rrule.MONTHLY,
            count=12,
            bymonthday=day,
            dtstart=start
        )
        
        occurrences = list(rule)
        
        # Check all occurrences are on the specified day (or last valid day of month)
        for occ in occurrences:
            # Get the last day of that month
            import calendar
            last_day = calendar.monthrange(occ.year, occ.month)[1]
            expected_day = min(day, last_day)
            assert occ.day == expected_day or occ.day == day
            
    except ValueError:
        # Some days might not be valid for all months
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])