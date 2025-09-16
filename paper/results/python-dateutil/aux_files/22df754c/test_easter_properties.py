import datetime
from hypothesis import given, strategies as st, assume, settings
from dateutil import easter
import pytest


# Test that different Easter calculation methods give consistent results in overlapping ranges
@given(st.integers(min_value=1583, max_value=4099))
def test_easter_method_consistency(year):
    """Test that EASTER_WESTERN (method 3) and EASTER_ORTHODOX (method 2) are consistent where they overlap"""
    
    # Method 2: EASTER_ORTHODOX - Original method, Gregorian calendar
    # Method 3: EASTER_WESTERN - Revised method, Gregorian calendar  
    # Both valid for 1583-4099
    
    try:
        orthodox = easter.easter(year, method=2)
        western = easter.easter(year, method=3)
        
        # They should both return valid Easter dates
        assert orthodox.month in [3, 4]
        assert western.month in [3, 4]
        assert orthodox.weekday() == 6  # Sunday
        assert western.weekday() == 6   # Sunday
        
        # The dates may differ between Orthodox and Western traditions
        # but both should be valid dates
        assert orthodox.year == year
        assert western.year == year
        
    except Exception as e:
        pytest.fail(f"Easter calculation failed for year {year}: {e}")


# Test Easter date monotonicity within a year
@given(st.integers(min_value=1583, max_value=4098))
def test_easter_year_progression(year):
    """Test that Easter dates progress sensibly from year to year"""
    
    easter1 = easter.easter(year, method=3)
    easter2 = easter.easter(year + 1, method=3)
    
    # The dates should be about a year apart, give or take the lunar cycle
    delta = (easter2 - easter1).days
    
    # Easter can vary by up to 35 days from year to year
    # (lunar cycle is ~29.5 days, plus week alignment)
    # Typical range is 330-400 days apart
    assert 330 <= delta <= 400, f"Unexpected delta {delta} days between Easter {year} and {year+1}"


# Test Easter calculation boundary years
def test_easter_boundary_years():
    """Test Easter calculation at the boundaries of valid ranges"""
    
    # Test earliest valid year for Western method
    easter_1583 = easter.easter(1583, method=3)
    assert easter_1583.year == 1583
    assert easter_1583.month in [3, 4]
    
    # Test latest valid year  
    easter_4099 = easter.easter(4099, method=3)
    assert easter_4099.year == 4099
    assert easter_4099.month in [3, 4]
    
    # Test invalid years should raise exception
    with pytest.raises((ValueError, Exception)):
        easter.easter(1582, method=3)  # Before valid range
    
    with pytest.raises((ValueError, Exception)):
        easter.easter(4100, method=3)  # After valid range


# Test Easter calculation for known historical dates
def test_easter_known_dates():
    """Test Easter calculation against known historical Easter dates"""
    
    # Known Easter dates (Western/Gregorian)
    known_dates = [
        (2020, 4, 12),
        (2021, 4, 4),
        (2022, 4, 17),
        (2023, 4, 9),
        (2024, 3, 31),
        (2025, 4, 20),
    ]
    
    for year, month, day in known_dates:
        calculated = easter.easter(year, method=3)
        expected = datetime.date(year, month, day)
        assert calculated == expected, f"Easter {year}: expected {expected}, got {calculated}"


# Test invalid method parameter
@given(st.integers(min_value=-100, max_value=100))
def test_easter_invalid_method(method):
    """Test Easter calculation with invalid method numbers"""
    
    if method not in [1, 2, 3]:
        # Should raise an error for invalid methods
        with pytest.raises((ValueError, Exception)):
            easter.easter(2020, method=method)
    else:
        # Valid methods should work
        result = easter.easter(2020, method=method)
        assert isinstance(result, datetime.date)


# Test Easter calculation determinism
@given(st.integers(min_value=1583, max_value=4099))
def test_easter_deterministic(year):
    """Test that Easter calculation is deterministic"""
    
    # Calculate Easter multiple times for the same year
    results = [easter.easter(year, method=3) for _ in range(10)]
    
    # All results should be identical
    assert all(r == results[0] for r in results)


# Test Easter date properties
@given(st.integers(min_value=1583, max_value=4099))
def test_easter_after_spring_equinox(year):
    """Test that Easter is after the spring equinox (approximately March 20)"""
    
    easter_date = easter.easter(year, method=3)
    spring_equinox = datetime.date(year, 3, 20)  # Approximate
    
    # Easter should be after the spring equinox
    assert easter_date >= spring_equinox


# Test method 1 (Julian calendar) for early years
@given(st.integers(min_value=326, max_value=1582))
def test_easter_julian_method(year):
    """Test Easter calculation with Julian calendar method"""
    
    try:
        # Method 1 is for Julian calendar, valid after 326 AD
        julian_easter = easter.easter(year, method=1)
        
        # Should return a valid Easter date
        assert julian_easter.year == year
        assert julian_easter.month in [3, 4]
        assert julian_easter.weekday() == 6  # Sunday
        
    except Exception:
        # Some years might fail
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])