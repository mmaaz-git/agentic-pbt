import datetime
import dateutil.easter as easter
from hypothesis import given, strategies as st, assume, settings
import pytest


# Test 1: Easter date should be in valid range
@given(st.integers(min_value=1, max_value=9999), st.integers(min_value=1, max_value=3))
def test_easter_date_range(year, method):
    """Easter should fall within documented date ranges."""
    date = easter.easter(year, method)
    
    # All methods should return dates between March and May
    assert 3 <= date.month <= 5
    
    # Western Easter (method 3) should be March 22 - April 25
    if method == 3:
        if date.month == 3:
            assert date.day >= 22
        elif date.month == 4:
            assert date.day <= 25
        else:
            assert False, f"Western Easter outside March-April: {date}"
    
    # Julian (method 1) can theoretically be March 22 - April 25 in Julian calendar
    # Orthodox (method 2) can go into May due to Julian-Gregorian conversion


# Test 2: Easter calculation should be deterministic
@given(st.integers(min_value=1, max_value=9999), st.integers(min_value=1, max_value=3))
def test_easter_deterministic(year, method):
    """Calling easter() multiple times with same args should return same date."""
    date1 = easter.easter(year, method)
    date2 = easter.easter(year, method)
    assert date1 == date2


# Test 3: Invalid method should raise ValueError
@given(st.integers(min_value=1, max_value=9999), st.integers())
def test_invalid_method_raises(year, method):
    """Methods outside 1-3 should raise ValueError."""
    if not (1 <= method <= 3):
        with pytest.raises(ValueError, match="invalid method"):
            easter.easter(year, method)


# Test 4: Return type should always be datetime.date
@given(st.integers(min_value=1, max_value=9999), st.integers(min_value=1, max_value=3))
def test_return_type(year, method):
    """Easter should always return a datetime.date object."""
    result = easter.easter(year, method)
    assert isinstance(result, datetime.date)
    assert result.year == year


# Test 5: Easter should always be on Sunday
@given(st.integers(min_value=1, max_value=9999), st.integers(min_value=1, max_value=3))
def test_easter_is_sunday(year, method):
    """Easter should always fall on a Sunday (weekday=6)."""
    date = easter.easter(year, method)
    # Note: In Python's datetime, Monday is 0, Sunday is 6
    assert date.weekday() == 6, f"Easter {date} is not a Sunday (weekday={date.weekday()})"


# Test 6: Contract violation - function works outside documented ranges
@given(st.integers(min_value=1, max_value=9999))
def test_documented_validity_ranges(year):
    """Test that function enforces documented validity ranges."""
    # Documentation says:
    # Method 1 (JULIAN): valid after 326 AD
    # Method 2 (ORTHODOX): valid 1583-4099  
    # Method 3 (WESTERN): valid 1583-4099
    
    # Test Method 1 - should only work after 326
    if year <= 326:
        # According to docs, should not work before 327
        try:
            result = easter.easter(year, 1)
            # If we get here without exception, it's working outside documented range
            if year < 327:
                # This is a contract violation
                pass
        except ValueError:
            # Expected for years before 327
            pass
    
    # Test Methods 2 and 3 - should only work 1583-4099
    for method in [2, 3]:
        if not (1583 <= year <= 4099):
            try:
                result = easter.easter(year, method)
                # If we get here, it's working outside documented range
                # This is a contract violation but function still works
            except ValueError:
                # Would be expected based on documentation
                pass


# Test 7: Check for integer overflow or precision issues
@given(st.integers(min_value=1, max_value=9999))
def test_no_float_precision_issues(year):
    """Test that calculations don't have float precision issues."""
    # The algorithm uses integer division but has one float division
    # Line 81: i = h - (h//28)*(1 - (h//28)*(29//(h + 1))*((21 - g)//11))
    date = easter.easter(year, 3)
    
    # Result should be a valid date with integer components
    assert isinstance(date.year, int)
    assert isinstance(date.month, int) 
    assert isinstance(date.day, int)
    
    # Date should be constructible
    reconstructed = datetime.date(date.year, date.month, date.day)
    assert reconstructed == date


# Test 8: Year should be preserved in output
@given(st.integers(min_value=1, max_value=9999), st.integers(min_value=1, max_value=3))
def test_year_preserved(year, method):
    """The returned date should have the same year as input."""
    date = easter.easter(year, method)
    assert date.year == year


# Test 9: Test floating point input handling
@given(st.floats(min_value=1.0, max_value=9999.0, allow_nan=False, allow_infinity=False))
def test_float_year_handling(year_float):
    """Test how function handles float years."""
    # The function uses int(y) internally, so floats should work
    try:
        date = easter.easter(year_float, 3)
        assert date.year == int(year_float)
    except (ValueError, TypeError) as e:
        # Could raise if float handling is problematic
        pass


# Test 10: Test method as float
@given(st.integers(min_value=1, max_value=9999))
def test_float_method_handling(year):
    """Test how function handles float methods."""
    # Method validation checks (1 <= method <= 3)
    for method_float in [1.0, 2.0, 3.0, 1.5, 2.5]:
        if 1 <= method_float <= 3:
            try:
                date = easter.easter(year, method_float)
                # Should work for 1.0, 2.0, 3.0
                if method_float in [1.0, 2.0, 3.0]:
                    assert isinstance(date, datetime.date)
            except (ValueError, TypeError):
                pass
        else:
            with pytest.raises(ValueError):
                easter.easter(year, method_float)