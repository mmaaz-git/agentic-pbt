import datetime
import dateutil.easter as easter
from hypothesis import given, strategies as st, settings
import pytest


# Bug 1: Invalid date calculation (June 31st doesn't exist)
@given(st.integers(min_value=1, max_value=9999), st.integers(min_value=1, max_value=3))
@settings(max_examples=10000)
def test_valid_date_generation(year, method):
    """Easter calculation should always produce valid dates."""
    # This should never raise ValueError for day out of range
    date = easter.easter(year, method)
    # If we get here, the date was valid
    assert isinstance(date, datetime.date)


# Bug 2: Julian Easter not on Sunday  
@given(st.integers(min_value=1, max_value=9999))
def test_julian_easter_sunday(year):
    """Julian Easter (method 1) should be on Sunday in Julian calendar."""
    date = easter.easter(year, 1)
    # The bug is that method 1 calculates Julian calendar Easter
    # but returns it as a Gregorian date, losing the Sunday property
    # This is a logic bug in the implementation
    
    # For years where Julian and Gregorian calendars diverge significantly,
    # the returned date won't be Sunday in Gregorian terms
    if year < 100:
        # Early years show this clearly - all return Tuesday
        assert date.weekday() != 6  # Demonstrating the bug


# Bug 3: Documentation contract violation
def test_orthodox_date_range():
    """Orthodox Easter can fall outside documented range (into June)."""
    # Documentation says Orthodox Easter is valid 1583-4099
    # and implies dates up to May 23
    # But we found June dates
    
    june_easter_found = False
    for year in [5175, 5992]:  # Known June Easter years
        date = easter.easter(year, 2)
        if date.month == 6:
            june_easter_found = True
            print(f"June Easter found: {year} -> {date}")
    
    assert june_easter_found, "June Easter exists, contradicting implied May 23 limit"


if __name__ == "__main__":
    # Demonstrate the specific bugs
    
    print("Bug 1: Invalid date generation")
    try:
        date = easter.easter(5243, 2)
        print(f"  Year 5243, method 2: {date}")
    except ValueError as e:
        print(f"  Year 5243, method 2: ValueError - {e}")
    
    print("\nBug 2: Julian Easter not on Sunday")
    for year in [1, 2, 3, 2024]:
        date = easter.easter(year, 1)
        weekday_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][date.weekday()]
        is_sunday = date.weekday() == 6
        print(f"  Year {year}: {date} ({weekday_name}) - Sunday: {is_sunday}")
    
    print("\nBug 3: June Easter (outside documented range)")
    for year in [5175, 5992]:
        date = easter.easter(year, 2)
        print(f"  Year {year}: {date} (month={date.month})")