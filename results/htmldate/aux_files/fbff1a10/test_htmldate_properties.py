#!/usr/bin/env python3
"""Property-based tests for htmldate library using Hypothesis."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the specific functions we want to test
from htmldate.extractors import correct_year, try_swap_values
from htmldate.validators import is_valid_format


# Test 1: correct_year function properties
@given(st.integers(min_value=0, max_value=99))
def test_correct_year_two_digit_conversion(year):
    """Test that correct_year properly converts 2-digit years to 4-digit years.
    
    According to the implementation:
    - Years >= 90 should become 19xx
    - Years < 90 should become 20xx
    """
    result = correct_year(year)
    
    # Property 1: Result should always be 4-digit year
    assert result >= 1900
    assert result <= 2099
    
    # Property 2: Conversion follows documented rules
    if year >= 90:
        assert result == 1900 + year
    else:
        assert result == 2000 + year


@given(st.integers(min_value=100, max_value=9999))
def test_correct_year_four_digit_unchanged(year):
    """Test that 4-digit years are not modified."""
    result = correct_year(year)
    assert result == year


# Test 2: try_swap_values function properties
@given(st.integers(min_value=1, max_value=31), st.integers(min_value=1, max_value=31))
def test_try_swap_values_properties(day, month):
    """Test the day/month swapping logic.
    
    According to the implementation:
    - If month > 12 and day <= 12, swap them
    - Otherwise, keep them as is
    """
    result_day, result_month = try_swap_values(day, month)
    
    # Property: Swapping happens iff month > 12 and day <= 12
    if month > 12 and day <= 12:
        assert result_day == month
        assert result_month == day
    else:
        assert result_day == day
        assert result_month == month


@given(st.integers(min_value=1, max_value=100), st.integers(min_value=1, max_value=100))
def test_try_swap_values_involutive_when_both_valid(day, month):
    """Test that swap is involutive under certain conditions."""
    assume(day <= 12 or month <= 12)  # At least one should be a valid month
    
    # First swap
    d1, m1 = try_swap_values(day, month)
    
    # Second swap
    d2, m2 = try_swap_values(d1, m1)
    
    # Property: If we started with invalid month but valid day as month candidate,
    # double swap should return to original
    if month > 12 and day <= 12:
        # After first swap: d1=month, m1=day
        # For second swap: d1 > 12 (since month > 12), m1 <= 12 (since day <= 12)
        # So no swap happens on second call
        assert d2 == d1 == month
        assert m2 == m1 == day


# Test 3: is_valid_format function properties
@given(st.text(min_size=1, max_size=50))
def test_is_valid_format_with_random_strings(format_string):
    """Test that is_valid_format correctly validates format strings."""
    result = is_valid_format(format_string)
    
    # If it returns True, the format should work with strftime
    if result:
        # Must contain % for strftime directives
        assert "%" in format_string
        
        # Should be able to format a date without error
        test_date = datetime(2017, 9, 1, 0, 0)
        try:
            formatted = test_date.strftime(format_string)
            assert formatted is not None
        except (ValueError, TypeError):
            # If strftime fails, is_valid_format should have returned False
            pytest.fail(f"is_valid_format returned True but strftime failed for: {format_string}")


@given(st.sampled_from(["%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%Y%m%d", "%B %d, %Y", "%d %B %Y"]))
def test_is_valid_format_known_good_formats(format_string):
    """Test that known valid format strings are accepted."""
    assert is_valid_format(format_string) == True


@given(st.sampled_from(["", "YYYY-MM-DD", "invalid", "2023-01-01", None]))
def test_is_valid_format_known_bad_formats(format_string):
    """Test that known invalid format strings are rejected."""
    # Note: None will cause TypeError in the actual function
    if format_string is None:
        # The function checks isinstance(outputformat, str) first
        assert is_valid_format(format_string) == False
    else:
        # Strings without % should be rejected
        assert is_valid_format(format_string) == False


# Test 4: Edge cases for correct_year
@given(st.integers())
def test_correct_year_with_any_integer(year):
    """Test correct_year handles any integer input."""
    result = correct_year(year)
    
    # It should return an integer
    assert isinstance(result, int)
    
    # For negative or very large years, should return unchanged
    if year < 0 or year >= 100:
        assert result == year


# Test 5: More extensive testing of try_swap_values edge cases
@given(st.integers(), st.integers())
def test_try_swap_values_handles_any_integers(day, month):
    """Test that try_swap_values handles any integer inputs without crashing."""
    result = try_swap_values(day, month)
    
    # Should always return a tuple of two values
    assert isinstance(result, tuple)
    assert len(result) == 2
    
    # The logic should still hold for any integers
    result_day, result_month = result
    if month > 12 and day <= 12:
        assert result_day == month
        assert result_month == day
    else:
        assert result_day == day
        assert result_month == month


if __name__ == "__main__":
    print("Running property-based tests for htmldate library...")
    
    # Run with more examples for thorough testing
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))