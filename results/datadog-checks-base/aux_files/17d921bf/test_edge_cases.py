"""More aggressive property-based tests to find edge case bugs"""

import math
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from hypothesis import given, strategies as st, assume, settings, example
import pytest


# --- Functions under test (same as before) ---

def ensure_bytes(s):
    """Convert input to bytes, ensuring UTF-8 encoding"""
    if isinstance(s, bytes):
        return s
    return s.encode('utf-8')


def ensure_unicode(s):
    """Convert input to unicode string, decoding from UTF-8 if needed"""
    if isinstance(s, bytes):
        return s.decode('utf-8')
    return str(s)


def compute_percent(part, total):
    """Calculate percentage by dividing part by total and multiplying by 100"""
    if total == 0:
        return 0.0
    return (part / total) * 100


def round_value(value, precision=0, rounding_method=ROUND_HALF_UP):
    """Round a numeric value to specified precision"""
    return float(Decimal(str(value)).quantize(Decimal(10) ** -precision, rounding=rounding_method))


def pattern_filter(items, whitelist=None, blacklist=None, key=None):
    """Filter list items using regex whitelist/blacklist patterns"""
    if key is None:
        key = lambda x: x
    
    if whitelist:
        items = [item for item in items if any(re.search(pattern, key(item)) for pattern in whitelist)]
    
    if blacklist:
        items = [item for item in items if not any(re.search(pattern, key(item)) for pattern in blacklist)]
    
    return items


# --- Aggressive edge case tests ---

# Test for special float values
@given(st.one_of(
    st.just(float('inf')),
    st.just(float('-inf')),
    st.just(float('nan')),
    st.floats(min_value=1e308, max_value=1e308)  # Near float max
))
def test_round_value_special_floats(value):
    """Test round_value with special float values"""
    try:
        result = round_value(value, 2)
        # If it doesn't raise, check if result is reasonable
        if not math.isnan(value):
            assert not math.isnan(result), f"Got NaN from non-NaN input {value}"
    except (InvalidOperation, OverflowError, ValueError):
        # These exceptions are acceptable for inf/nan
        pass


# Test ensure_unicode with integers and other types
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=True, allow_infinity=True),
    st.booleans(),
    st.none()
))
def test_ensure_unicode_non_string_types(value):
    """ensure_unicode should handle non-string types"""
    result = ensure_unicode(value)
    assert isinstance(result, str), f"Failed to convert {type(value)} to str"
    # Check the conversion is reasonable
    assert str(value) == result, f"Unexpected conversion: {value} -> {result}"


# Test pattern_filter with regex special characters
@given(
    st.lists(st.text()),
    st.lists(st.sampled_from(['[', ']', '(', ')', '*', '+', '?', '{', '}', '\\', '|', '^', '$', '.']))
)
def test_pattern_filter_regex_special_chars(items, special_chars):
    """Test pattern_filter with regex special characters that might cause issues"""
    whitelist = [''.join(special_chars)] if special_chars else None
    try:
        result = pattern_filter(items, whitelist, None)
        # If it doesn't crash, that's already good
        assert isinstance(result, list)
    except re.error:
        # Invalid regex is expected for some special character combinations
        pass


# Test compute_percent with very large numbers
@given(
    st.floats(min_value=1e300, max_value=1e308, allow_nan=False),
    st.floats(min_value=1e300, max_value=1e308, allow_nan=False)
)
def test_compute_percent_large_numbers(part, total):
    """Test compute_percent with very large numbers that might overflow"""
    result = compute_percent(part, total)
    # Check for overflow/underflow issues
    assert not math.isnan(result), f"Got NaN from valid inputs"
    assert not math.isinf(result), f"Got infinity from finite inputs"


# Test round_value with negative precision
@given(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    st.integers(min_value=-5, max_value=-1)
)
def test_round_value_negative_precision(value, precision):
    """Test round_value with negative precision (rounding to tens, hundreds, etc.)"""
    try:
        result = round_value(value, precision)
        # Verify it's actually rounded to the right scale
        scale = 10 ** (-precision)
        # Check if result is a multiple of scale (within floating point tolerance)
        if value != 0:
            remainder = abs(result) % scale
            assert remainder < 1e-9 or abs(remainder - scale) < 1e-9, \
                f"Not properly rounded to scale {scale}: {result}"
    except (InvalidOperation, OverflowError):
        # May fail for extreme values
        pass


# Test ensure_bytes with already-encoded strings containing unicode
@given(st.text(alphabet=st.characters(min_codepoint=0x1F600, max_codepoint=0x1F64F)))  # Emoji range
def test_ensure_bytes_unicode_emoji(text):
    """Test ensure_bytes with emoji and high unicode characters"""
    result = ensure_bytes(text)
    assert isinstance(result, bytes)
    # Should be able to decode back
    decoded = result.decode('utf-8')
    assert decoded == text, f"Lost data in encoding: {text} != {decoded}"


# Test pattern_filter with empty pattern lists
@given(st.lists(st.text()))
def test_pattern_filter_empty_patterns(items):
    """Test pattern_filter with empty whitelist/blacklist"""
    # Empty lists should be different from None
    result_empty = pattern_filter(items, [], [])
    result_none = pattern_filter(items, None, None)
    
    # With empty whitelist, nothing should pass
    assert result_empty == [], f"Empty whitelist should filter everything"
    # With None, everything should pass
    assert result_none == items, f"None filters should pass everything"


# Test compute_percent with negative numbers
@given(
    st.floats(min_value=-1e10, max_value=0, allow_nan=False),
    st.floats(min_value=-1e10, max_value=-1e-10, allow_nan=False)
)
def test_compute_percent_negative_numbers(part, total):
    """Test compute_percent with negative numbers"""
    result = compute_percent(part, total)
    expected = (part / total) * 100
    assert math.isclose(result, expected, rel_tol=1e-9), \
        f"Incorrect result for negative numbers: {result} != {expected}"


# Test round_value with string representations of special values
@given(st.sampled_from(['1e308', '-1e308', '0.0', '-0.0', '1e-308']))
def test_round_value_string_edge_cases(value_str):
    """Test round_value with string representations of edge case numbers"""
    try:
        result = round_value(float(value_str), 2)
        assert isinstance(result, float)
        # For very large/small numbers, rounding might not change the value much
        if abs(float(value_str)) < 1e100:
            # Check that rounding actually happened
            decimal_places = str(result).split('.')[-1] if '.' in str(result) else ''
            # Scientific notation handling
            if 'e' not in str(result).lower():
                assert len(decimal_places) <= 2, f"Not properly rounded to 2 places: {result}"
    except (InvalidOperation, OverflowError, ValueError):
        # Some edge cases might fail
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])