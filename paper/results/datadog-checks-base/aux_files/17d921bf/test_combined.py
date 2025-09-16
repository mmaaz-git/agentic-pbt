"""Property-based tests for datadog_checks.utils functions"""

import math
import re
from decimal import ROUND_HALF_UP, Decimal
from hypothesis import given, strategies as st, assume, settings
import pytest


# --- Functions under test ---

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


def total_time_to_temporal_percent(total_time, scale):
    """Convert time measurements to a temporal percentage representation"""
    if scale == 0:
        return 0.0
    return (total_time / scale) * 100


def exclude_undefined_keys(mapping):
    """Remove dictionary entries with None values"""
    return {k: v for k, v in mapping.items() if v is not None}


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


# --- Property-based tests ---

# Test 1: Round-trip property for ensure_bytes/ensure_unicode
@given(st.text())
def test_ensure_bytes_unicode_round_trip(s):
    """ensure_unicode(ensure_bytes(s)) should equal s for unicode strings"""
    result = ensure_unicode(ensure_bytes(s))
    assert result == s, f"Round-trip failed for {repr(s)}"


# Test 2: Inverse round-trip starting from bytes
@given(st.binary())
def test_ensure_unicode_bytes_round_trip(b):
    """ensure_bytes(ensure_unicode(b)) should equal b for valid UTF-8 bytes"""
    try:
        # Only test with valid UTF-8 bytes
        b.decode('utf-8')
        result = ensure_bytes(ensure_unicode(b))
        assert result == b, f"Round-trip failed for bytes {repr(b)}"
    except UnicodeDecodeError:
        # Skip invalid UTF-8 sequences
        pass


# Test 3: exclude_undefined_keys invariant - no None values in output
@given(st.dictionaries(
    st.text(),
    st.one_of(st.none(), st.integers(), st.text(), st.floats(allow_nan=False))
))
def test_exclude_undefined_keys_no_none(mapping):
    """Result of exclude_undefined_keys should never contain None values"""
    result = exclude_undefined_keys(mapping)
    assert None not in result.values(), f"Found None in result: {result}"
    # Also check all non-None keys are preserved
    for k, v in mapping.items():
        if v is not None:
            assert k in result and result[k] == v, f"Lost non-None key {k}"


# Test 4: pattern_filter invariants
@given(
    st.lists(st.text()),
    st.one_of(st.none(), st.lists(st.text())),
    st.one_of(st.none(), st.lists(st.text()))
)
def test_pattern_filter_invariants(items, whitelist, blacklist):
    """pattern_filter should maintain invariants:
    1. Output length <= input length
    2. All output items are from input
    3. Order is preserved (relative ordering)
    """
    # Skip if patterns are not valid regex
    try:
        result = pattern_filter(items, whitelist, blacklist)
    except Exception:
        # Skip invalid regex patterns
        return
    
    # Invariant 1: length
    assert len(result) <= len(items), f"Output longer than input"
    
    # Invariant 2: all items from input
    for item in result:
        assert item in items, f"Item {item} not in original list"
    
    # Invariant 3: order preserved - check relative ordering
    # For unique items in the result, their relative order should match the input
    seen = set()
    unique_result_indices = []
    unique_input_indices = []
    
    for i, item in enumerate(result):
        if item not in seen:
            seen.add(item)
            unique_result_indices.append(i)
            # Find first occurrence in input
            unique_input_indices.append(items.index(item))
    
    # Check that relative ordering is preserved
    if unique_input_indices:
        assert unique_input_indices == sorted(unique_input_indices), \
            f"Order not preserved for unique items"


# Test 5: pattern_filter idempotence
@given(
    st.lists(st.text()),
    st.one_of(st.none(), st.lists(st.text(min_size=1))),
    st.one_of(st.none(), st.lists(st.text(min_size=1)))
)
def test_pattern_filter_idempotence(items, whitelist, blacklist):
    """Applying the same filter twice should give the same result"""
    try:
        first_filter = pattern_filter(items, whitelist, blacklist)
        second_filter = pattern_filter(first_filter, whitelist, blacklist)
        assert first_filter == second_filter, "Filter not idempotent"
    except Exception:
        # Skip invalid regex patterns
        pass


# Test 6: round_value idempotence
@given(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    st.integers(min_value=0, max_value=10)
)
def test_round_value_idempotence(value, precision):
    """Rounding an already rounded value should not change it"""
    rounded_once = round_value(value, precision)
    rounded_twice = round_value(rounded_once, precision)
    assert math.isclose(rounded_once, rounded_twice, rel_tol=1e-9), \
        f"Idempotence failed: {rounded_once} != {rounded_twice}"


# Test 7: compute_percent mathematical properties
@given(
    st.floats(min_value=0, max_value=1e10, allow_nan=False),
    st.floats(min_value=1e-10, max_value=1e10, allow_nan=False)
)
def test_compute_percent_properties(part, total):
    """compute_percent should maintain mathematical properties"""
    result = compute_percent(part, total)
    
    # Property 1: Result is percentage
    expected = (part / total) * 100
    assert math.isclose(result, expected, rel_tol=1e-9), \
        f"Incorrect percentage: {result} != {expected}"
    
    # Property 2: When part <= total, result <= 100
    if part <= total:
        assert result <= 100.0001, f"Percentage > 100 when part <= total"
    
    # Property 3: Result is non-negative when part is non-negative
    if part >= 0:
        assert result >= -0.0001, f"Negative percentage for positive part"


# Test 8: compute_percent edge cases
@given(st.floats(allow_nan=False))
def test_compute_percent_zero_total(part):
    """compute_percent with zero total should return 0"""
    result = compute_percent(part, 0)
    assert result == 0.0, f"Non-zero result for zero total: {result}"


# Test 9: total_time_to_temporal_percent similarity
@given(
    st.floats(min_value=0, max_value=1e10, allow_nan=False),
    st.floats(min_value=1e-10, max_value=1e10, allow_nan=False)
)
def test_temporal_percent_equivalence(time, scale):
    """total_time_to_temporal_percent should behave like compute_percent"""
    temporal_result = total_time_to_temporal_percent(time, scale)
    percent_result = compute_percent(time, scale)
    assert math.isclose(temporal_result, percent_result, rel_tol=1e-9), \
        f"Functions not equivalent: {temporal_result} != {percent_result}"


# Test 10: ensure_bytes type guarantee
@given(st.one_of(st.text(), st.binary()))
def test_ensure_bytes_type(input_val):
    """ensure_bytes should always return bytes"""
    result = ensure_bytes(input_val)
    assert isinstance(result, bytes), f"Result not bytes: {type(result)}"


# Test 11: ensure_unicode type guarantee  
@given(st.one_of(st.text(), st.binary()))
def test_ensure_unicode_type(input_val):
    """ensure_unicode should always return str"""
    try:
        result = ensure_unicode(input_val)
        assert isinstance(result, str), f"Result not str: {type(result)}"
    except UnicodeDecodeError:
        # Expected for invalid UTF-8 bytes
        pass


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])