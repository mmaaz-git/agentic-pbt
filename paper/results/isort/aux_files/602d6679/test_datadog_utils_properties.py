#!/usr/bin/env python3
"""Property-based tests for datadog_checks.utils using Hypothesis."""

import datetime
import math
import sys
import os

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/datadog-checks-base_env/lib/python3.13/site-packages')

from decimal import ROUND_HALF_UP, ROUND_DOWN, ROUND_UP
from hypothesis import assume, given, strategies as st, settings
import pytest

# Import functions to test
from datadog_checks.base.utils.common import (
    ensure_bytes, ensure_unicode, compute_percent, round_value,
    pattern_filter, total_time_to_temporal_percent, exclude_undefined_keys
)
from datadog_checks.base.utils.date import parse_rfc3339, format_rfc3339
from datadog_checks.base.utils.format.json import decode, encode, encode_bytes
from datadog_checks.base.utils.functions import identity, predicate, return_true, return_false


# Test 1: ensure_bytes/ensure_unicode round-trip property
@given(st.text())
def test_ensure_unicode_bytes_roundtrip(s):
    """Test that ensure_bytes and ensure_unicode are inverse operations."""
    # String -> bytes -> string
    bytes_val = ensure_bytes(s)
    back_to_str = ensure_unicode(bytes_val)
    assert back_to_str == s
    
    # Also test bytes -> string -> bytes
    original_bytes = s.encode('utf-8')
    str_val = ensure_unicode(original_bytes)
    back_to_bytes = ensure_bytes(str_val)
    assert back_to_bytes == original_bytes


# Test 2: JSON encode/decode round-trip property
@given(st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False, allow_infinity=False) | st.text(),
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
    max_leaves=50
))
def test_json_encode_decode_roundtrip(obj):
    """Test that JSON encode and decode are inverse operations."""
    encoded = encode(obj)
    decoded = decode(encoded)
    assert decoded == obj
    
    # Also test with bytes encoding
    encoded_bytes = encode_bytes(obj)
    decoded_from_bytes = decode(encoded_bytes)
    assert decoded_from_bytes == obj


# Test 3: RFC3339 date parse/format round-trip property
@given(st.datetimes(min_value=datetime.datetime(1900, 1, 1), max_value=datetime.datetime(2100, 1, 1)))
def test_rfc3339_parse_format_roundtrip(dt):
    """Test that RFC3339 format and parse are inverse operations."""
    # Add UTC timezone if not present
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    
    formatted = format_rfc3339(dt)
    parsed = parse_rfc3339(formatted)
    
    # Compare with microsecond precision
    assert parsed.replace(microsecond=0) == dt.replace(microsecond=0)


# Test 4: pattern_filter invariants
@given(
    st.lists(st.text(min_size=1)),
    st.lists(st.text(min_size=1)),
    st.lists(st.text(min_size=1))
)
def test_pattern_filter_blacklist_precedence(items, whitelist, blacklist):
    """Test that blacklist takes precedence over whitelist in pattern_filter."""
    assume(len(items) > 0)
    
    # Create regex patterns that match everything (for simplicity)
    whitelist_patterns = ['.*'] if whitelist else None
    blacklist_patterns = blacklist if blacklist else None
    
    result = pattern_filter(items, whitelist=whitelist_patterns, blacklist=blacklist_patterns)
    
    # If blacklist is provided, no item matching blacklist should be in result
    if blacklist_patterns:
        for pattern in blacklist_patterns:
            for item in result:
                # Check if any blacklist pattern matches this item
                import re
                if re.search(pattern, item):
                    # This shouldn't happen - blacklist should have filtered it out
                    assert False, f"Item {item} matches blacklist pattern {pattern} but wasn't filtered"
    
    # Result should be a subset of original items
    assert set(result).issubset(set(items))


@given(st.lists(st.text(min_size=1)))
def test_pattern_filter_subset_invariant(items):
    """Test that filtered results are always a subset of original items."""
    # Test with various filter combinations
    result_no_filter = pattern_filter(items)
    assert result_no_filter == items
    
    result_whitelist = pattern_filter(items, whitelist=['.*'])
    assert set(result_whitelist).issubset(set(items))
    
    result_blacklist = pattern_filter(items, blacklist=['test'])
    assert set(result_blacklist).issubset(set(items))


# Test 5: round_value mathematical properties
@given(
    st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.integers(min_value=0, max_value=10)
)
def test_round_value_idempotence(value, precision):
    """Test that rounding twice gives the same result (idempotence)."""
    rounded_once = round_value(value, precision)
    rounded_twice = round_value(rounded_once, precision)
    assert math.isclose(rounded_once, rounded_twice, rel_tol=1e-9)


@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_round_value_rounding_methods(value):
    """Test different rounding methods produce expected relationships."""
    # ROUND_DOWN should be <= ROUND_HALF_UP <= ROUND_UP
    down = round_value(value, 0, ROUND_DOWN)
    half_up = round_value(value, 0, ROUND_HALF_UP)
    up = round_value(value, 0, ROUND_UP)
    
    if value >= 0:
        assert down <= half_up <= up
    else:
        assert up <= half_up <= down


# Test 6: compute_percent mathematical properties
@given(
    st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.01, max_value=1e10, allow_nan=False, allow_infinity=False)
)
def test_compute_percent_range(part, total):
    """Test that compute_percent returns values in valid range."""
    result = compute_percent(part, total)
    
    # Percentage should be between 0 and 100 when part <= total
    if part <= total:
        assert 0 <= result <= 100
    
    # When part > total, percentage > 100
    if part > total:
        assert result > 100


@given(st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_compute_percent_zero_total(part):
    """Test that compute_percent handles zero total correctly."""
    result = compute_percent(part, 0)
    assert result == 0


# Test 7: identity function property
@given(st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_identity_function(obj):
    """Test that identity function returns its input unchanged."""
    result = identity(obj)
    assert result is obj
    
    # Test with kwargs (should be ignored)
    result_with_kwargs = identity(obj, foo='bar', baz=123)
    assert result_with_kwargs is obj


# Test 8: predicate function properties  
@given(st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_predicate_function(obj):
    """Test that predicate function returns correct boolean functions."""
    pred = predicate(obj)
    
    # Check that it returns the right function
    if bool(obj):
        assert pred is return_true
        assert pred() is True
    else:
        assert pred is return_false
        assert pred() is False


# Test 9: exclude_undefined_keys property
@given(st.dictionaries(
    st.text(),
    st.one_of(st.none(), st.integers(), st.text(), st.booleans())
))
def test_exclude_undefined_keys(mapping):
    """Test that exclude_undefined_keys removes only None values."""
    result = exclude_undefined_keys(mapping)
    
    # Check no None values in result
    assert None not in result.values()
    
    # Check all non-None values are preserved
    for key, value in mapping.items():
        if value is not None:
            assert key in result
            assert result[key] == value
        else:
            assert key not in result


# Test 10: total_time_to_temporal_percent mathematical property
@given(
    st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.integers(min_value=1, max_value=10000)
)
def test_total_time_to_temporal_percent(total_time, scale):
    """Test mathematical properties of temporal percent calculation."""
    result = total_time_to_temporal_percent(total_time, scale)
    
    # Result should be total_time / scale * 100
    expected = total_time / scale * 100
    assert math.isclose(result, expected, rel_tol=1e-9)
    
    # Test with default scale (1000 ms)
    result_default = total_time_to_temporal_percent(total_time)
    expected_default = total_time / 1000 * 100
    assert math.isclose(result_default, expected_default, rel_tol=1e-9)


if __name__ == "__main__":
    print("Running property-based tests for datadog_checks.utils...")
    pytest.main([__file__, "-v", "--tb=short"])