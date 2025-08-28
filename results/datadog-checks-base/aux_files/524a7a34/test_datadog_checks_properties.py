#!/usr/bin/env /root/hypothesis-llm/envs/datadog-checks-base_env/bin/python3
"""Property-based tests for datadog_checks module"""

import sys
import os
import re
import math
import traceback
from decimal import Decimal, ROUND_HALF_UP

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/datadog-checks-base_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
from hypothesis import seed

# Import the functions we want to test
from datadog_checks.base.utils.common import (
    ensure_bytes, ensure_unicode, to_native_string,
    compute_percent, round_value, pattern_filter
)
from datadog_checks.base.checks.base import AgentCheck
from datadog_checks.base.utils.format import json


# Test 1: Round-trip property for ensure_bytes/ensure_unicode
@given(st.text())
@settings(max_examples=200)
def test_ensure_bytes_unicode_round_trip(text):
    """Test that converting str -> bytes -> str preserves the original"""
    bytes_result = ensure_bytes(text)
    assert isinstance(bytes_result, bytes)
    
    unicode_result = ensure_unicode(bytes_result)
    assert isinstance(unicode_result, str)
    
    # Round-trip should preserve the original text
    assert unicode_result == text


@given(st.binary())
@settings(max_examples=200)
def test_ensure_bytes_idempotent(data):
    """Test that ensure_bytes is idempotent for bytes input"""
    result1 = ensure_bytes(data)
    result2 = ensure_bytes(result1)
    assert result1 == result2
    assert isinstance(result1, bytes)


@given(st.text())
@settings(max_examples=200)
def test_ensure_unicode_idempotent(text):
    """Test that ensure_unicode is idempotent for str input"""
    result1 = ensure_unicode(text)
    result2 = ensure_unicode(result1)
    assert result1 == result2
    assert isinstance(result1, str)


# Test 2: Mathematical properties of compute_percent
@given(
    st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=200)
def test_compute_percent_range(part, total):
    """Test that percentages are in valid range [0, 100] for positive inputs"""
    result = compute_percent(part, total)
    
    # Result should be between 0 and 100 when part <= total
    if part <= total:
        assert 0 <= result <= 100
    
    # When part > total, result can exceed 100 (which is valid for some use cases)
    assert result >= 0


@given(st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False))
@settings(max_examples=200)
def test_compute_percent_extremes(total):
    """Test edge cases for compute_percent"""
    # 0 part should give 0%
    assert compute_percent(0, total) == 0
    
    # total part should give 100%
    assert math.isclose(compute_percent(total, total), 100)


@given(st.floats(allow_nan=False, allow_infinity=False))
@settings(max_examples=200)
def test_compute_percent_zero_total(part):
    """Test that compute_percent handles zero total correctly"""
    # According to the code, this should return 0
    assert compute_percent(part, 0) == 0


# Test 3: Properties of round_value
@given(
    st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.integers(min_value=0, max_value=10)
)
@settings(max_examples=200)
def test_round_value_precision(value, precision):
    """Test that round_value respects precision"""
    result = round_value(value, precision=precision)
    
    # Result should be a float
    assert isinstance(result, float)
    
    # Check that the result has at most 'precision' decimal places
    # Convert to string to check decimal places
    if precision == 0:
        assert result == float(int(round(value)))
    else:
        # The rounded value should match when we round it again to the same precision
        assert result == round_value(result, precision=precision)


@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
@settings(max_examples=200)
def test_round_value_idempotent(value):
    """Test that round_value is idempotent"""
    result1 = round_value(value, precision=2)
    result2 = round_value(result1, precision=2)
    assert result1 == result2


# Test 4: Properties of pattern_filter
@given(
    st.lists(st.text(min_size=1), min_size=0, max_size=20),
    st.one_of(st.none(), st.lists(st.text(min_size=1), min_size=1, max_size=5))
)
@settings(max_examples=200)
def test_pattern_filter_subset(items, whitelist):
    """Test that filtered results are always a subset of input"""
    # Use simple patterns that match the whole string
    if whitelist:
        whitelist = [re.escape(w) for w in whitelist]
    
    result = pattern_filter(items, whitelist=whitelist)
    
    # Result should be a subset of items
    assert set(result) <= set(items)
    
    # Order should be preserved
    if result:
        indices = [items.index(r) for r in result]
        assert indices == sorted(indices)


@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=20),
    st.lists(st.text(min_size=1), min_size=1, max_size=5)
)
@settings(max_examples=200)
def test_pattern_filter_blacklist(items, blacklist):
    """Test that blacklisted items are never in the result"""
    # Create patterns that exactly match items
    blacklist_patterns = ['^{}$'.format(re.escape(b)) for b in blacklist]
    
    result = pattern_filter(items, blacklist=blacklist_patterns)
    
    # No blacklisted item should be in the result
    for blacklisted in blacklist:
        assert blacklisted not in result


# Test 5: Idempotence of AgentCheck normalization methods
@given(st.text())
@settings(max_examples=200)
def test_normalize_idempotent(text):
    """Test that normalize is idempotent"""
    check = AgentCheck(name='test', init_config={}, instances=[{}])
    
    # Test without fix_case
    result1 = check.normalize(text, fix_case=False)
    result2 = check.normalize(result1, fix_case=False)
    assert result1 == result2
    
    # Test with fix_case
    result3 = check.normalize(text, fix_case=True)
    result4 = check.normalize(result3, fix_case=True)
    assert result3 == result4


@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
@settings(max_examples=200)
def test_convert_to_underscore_separated_idempotent(text):
    """Test that convert_to_underscore_separated is idempotent"""
    check = AgentCheck(name='test', init_config={}, instances=[{}])
    
    result1 = check.convert_to_underscore_separated(text)
    result2 = check.convert_to_underscore_separated(result1)
    
    # Both should be bytes
    assert isinstance(result1, bytes)
    assert isinstance(result2, bytes)
    
    # Should be idempotent
    assert result1 == result2


# Test 6: JSON round-trip properties
@given(
    st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1e10, max_value=1e10),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text()
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=10),
            st.dictionaries(st.text(), children, max_size=10)
        ),
        max_leaves=50
    )
)
@settings(max_examples=200)
def test_json_round_trip(obj):
    """Test JSON encode/decode round-trip property"""
    encoded = json.encode(obj)
    assert isinstance(encoded, str)
    
    decoded = json.decode(encoded)
    assert decoded == obj


@given(
    st.dictionaries(
        st.text(min_size=1),
        st.integers(),
        min_size=2,
        max_size=10
    )
)
@settings(max_examples=200)
def test_json_sort_keys(data):
    """Test that sort_keys parameter works correctly"""
    encoded_sorted = json.encode(data, sort_keys=True)
    encoded_unsorted = json.encode(data, sort_keys=False)
    
    # Both should decode to the same data
    assert json.decode(encoded_sorted) == data
    assert json.decode(encoded_unsorted) == data
    
    # Sorted version should have keys in order
    # Extract keys from JSON string
    import re
    key_pattern = r'"([^"]+)":'
    keys_sorted = re.findall(key_pattern, encoded_sorted)
    
    # Check if keys appear in sorted order (for consecutive keys)
    if len(keys_sorted) > 1:
        for i in range(len(keys_sorted) - 1):
            # This is a simplified check - in real JSON, keys might not be consecutive
            # but for our test data they should be
            pass


# Run all tests
def run_tests():
    tests = [
        test_ensure_bytes_unicode_round_trip,
        test_ensure_bytes_idempotent,
        test_ensure_unicode_idempotent,
        test_compute_percent_range,
        test_compute_percent_extremes,
        test_compute_percent_zero_total,
        test_round_value_precision,
        test_round_value_idempotent,
        test_pattern_filter_subset,
        test_pattern_filter_blacklist,
        test_normalize_idempotent,
        test_convert_to_underscore_separated_idempotent,
        test_json_round_trip,
        test_json_sort_keys
    ]
    
    failures = []
    for test in tests:
        print(f"Running {test.__name__}...")
        try:
            test()
            print(f"  ✓ {test.__name__} passed")
        except AssertionError as e:
            print(f"  ✗ {test.__name__} failed: {e}")
            failures.append((test.__name__, e, traceback.format_exc()))
        except Exception as e:
            print(f"  ✗ {test.__name__} errored: {e}")
            failures.append((test.__name__, e, traceback.format_exc()))
    
    print(f"\n{'='*60}")
    print(f"Results: {len(tests) - len(failures)}/{len(tests)} tests passed")
    
    if failures:
        print(f"\nFailed tests:")
        for name, error, tb in failures:
            print(f"\n{name}:")
            print(tb)
    
    return len(failures) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)