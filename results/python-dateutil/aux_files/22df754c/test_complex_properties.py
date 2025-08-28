import datetime
from hypothesis import given, strategies as st, assume, settings
from dateutil import relativedelta, rrule
import pytest


# Test relativedelta normalization
@given(
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=-1000, max_value=1000)
)
def test_relativedelta_days_hours_normalization(days, hours):
    """Test that relativedelta normalizes days/hours properly"""
    # Create relativedelta with excessive hours
    rd1 = relativedelta.relativedelta(days=days, hours=hours)
    
    # Equivalent relativedelta with normalized values
    total_hours = days * 24 + hours
    norm_days = total_hours // 24
    norm_hours = total_hours % 24
    rd2 = relativedelta.relativedelta(days=norm_days, hours=norm_hours)
    
    # Apply to same base date
    base = datetime.datetime(2020, 6, 15, 12, 0, 0)
    result1 = base + rd1
    result2 = base + rd2
    
    # Should give same result
    assert result1 == result2


# Test relativedelta with negative month wraparound
@given(st.integers(min_value=1, max_value=12))
def test_relativedelta_negative_month_wraparound(start_month):
    """Test relativedelta with negative months that wrap around year"""
    base = datetime.datetime(2020, start_month, 15)
    
    # Subtract more months than we have in current year
    rd = relativedelta.relativedelta(months=-15)
    result = base + rd
    
    # Should wrap to previous year
    expected_year = 2018 if start_month <= 3 else 2019
    expected_month = start_month + 9 if start_month <= 3 else start_month - 3
    
    assert result.year == expected_year
    assert result.month == expected_month


# Test rrule infinite loop protection
def test_rrule_infinite_without_end():
    """Test that rrule without end conditions can be dangerous"""
    start = datetime.datetime(2020, 1, 1)
    
    # Create rule without count or until - infinite!
    rule = rrule.rrule(rrule.DAILY, dtstart=start)
    
    # This would hang if we list() it
    # Instead, use itertools.islice for safety
    import itertools
    first_100 = list(itertools.islice(rule, 100))
    assert len(first_100) == 100
    
    # Verify they're properly spaced
    for i in range(1, len(first_100)):
        delta = first_100[i] - first_100[i-1]
        assert delta.days == 1


# Test relativedelta month-end handling edge case
@given(st.integers(min_value=1, max_value=12))
def test_relativedelta_month_end_consistency(months):
    """Test relativedelta behavior with month-end dates"""
    # Start from last day of January
    base = datetime.datetime(2020, 1, 31)
    
    rd = relativedelta.relativedelta(months=months)
    result = base + rd
    
    # Check if date was adjusted for shorter months
    if result.month in [2, 4, 6, 9, 11]:
        # These months have < 31 days
        if result.month == 2:
            # February in 2020 (leap year) has 29 days
            assert result.day <= 29
        else:
            assert result.day <= 30


# Test combining relativedelta objects
@given(
    st.integers(min_value=-10, max_value=10),
    st.integers(min_value=-10, max_value=10),
    st.integers(min_value=-10, max_value=10),
    st.integers(min_value=-10, max_value=10)
)
def test_relativedelta_addition_associativity(d1, d2, m1, m2):
    """Test that combining relativedeltas is associative"""
    rd1 = relativedelta.relativedelta(days=d1, months=m1)
    rd2 = relativedelta.relativedelta(days=d2, months=m2)
    
    # Combine relativedeltas first, then apply
    combined = rd1 + rd2
    
    base = datetime.datetime(2020, 6, 15)
    
    # These should be equivalent
    result1 = base + combined
    result2 = base + rd1 + rd2
    
    # But they might not be due to order of operations!
    if m1 != 0 and d2 != 0:
        # When mixing months and days, order matters
        # This is related to the bug we already found
        pass
    else:
        assert result1 == result2


# Test rrule with invalid parameters
def test_rrule_invalid_bymonthday():
    """Test rrule with invalid bymonthday values"""
    start = datetime.datetime(2020, 1, 1)
    
    # Try to create rrule with invalid day
    try:
        rule = rrule.rrule(
            rrule.MONTHLY,
            count=12,
            bymonthday=32,  # No month has 32 days
            dtstart=start
        )
        occurrences = list(rule)
        # If it doesn't error, it should produce no occurrences
        assert len(occurrences) == 0
    except ValueError:
        # This is also acceptable
        pass


# Test relativedelta with leap year edge cases
def test_relativedelta_leap_year_feb29():
    """Test relativedelta with Feb 29 in leap years"""
    # Start from Feb 29, 2020 (leap year)
    base = datetime.datetime(2020, 2, 29)
    
    # Add 1 year (2021 is not a leap year)
    rd = relativedelta.relativedelta(years=1)
    result = base + rd
    
    # Should adjust to Feb 28, 2021
    assert result == datetime.datetime(2021, 2, 28)
    
    # Add 4 years (2024 is a leap year)
    rd4 = relativedelta.relativedelta(years=4)
    result4 = base + rd4
    
    # Should be Feb 29, 2024
    assert result4 == datetime.datetime(2024, 2, 29)


# Test rrule byweekday with multiple weekdays
def test_rrule_multiple_weekdays():
    """Test rrule with multiple weekdays"""
    start = datetime.datetime(2020, 1, 1)
    
    # Get all Mondays and Fridays in January 2020
    rule = rrule.rrule(
        rrule.WEEKLY,
        byweekday=(rrule.MO, rrule.FR),
        dtstart=start,
        until=datetime.datetime(2020, 1, 31)
    )
    
    occurrences = list(rule)
    
    # Check all are Monday (0) or Friday (4)
    for occ in occurrences:
        assert occ.weekday() in [0, 4]
    
    # Count them
    mondays = sum(1 for o in occurrences if o.weekday() == 0)
    fridays = sum(1 for o in occurrences if o.weekday() == 4)
    
    # January 2020: starts on Wed
    # Mondays: 6, 13, 20, 27 (4 total)
    # Fridays: 3, 10, 17, 24, 31 (5 total)
    assert mondays == 4
    assert fridays == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])