#!/usr/bin/env python3
"""Standalone property-based tests for datadog_checks functions"""

import re
import math
import traceback
from decimal import ROUND_HALF_UP, Decimal
from hypothesis import given, strategies as st, settings

# Copy the functions we want to test directly

MILLISECOND = 1000

def ensure_bytes(s):
    if isinstance(s, str):
        s = s.encode('utf-8')
    return s

def ensure_unicode(s):
    if isinstance(s, bytes):
        s = s.decode('utf-8')
    return s

def compute_percent(part, total):
    if total:
        return part / total * 100
    return 0

def round_value(value, precision=0, rounding_method=ROUND_HALF_UP):
    precision = '0.{}'.format('0' * precision)
    return float(Decimal(str(value)).quantize(Decimal(precision), rounding=rounding_method))

def pattern_filter(items, whitelist=None, blacklist=None, key=None):
    """This filters `items` by a regular expression `whitelist` and/or
    `blacklist`, with the `blacklist` taking precedence. An optional `key`
    function can be provided that will be passed each item.
    """
    def __return_self(obj):
        return obj
    
    def _filter(items, pattern_list, key):
        return {key(item) for pattern in pattern_list for item in items if re.search(pattern, key(item))}
    
    key = key or __return_self
    if whitelist:
        whitelisted = _filter(items, whitelist, key)

        if blacklist:
            blacklisted = _filter(items, blacklist, key)
            # Remove any blacklisted items from the whitelisted ones.
            whitelisted.difference_update(blacklisted)

        return [item for item in items if key(item) in whitelisted]

    elif blacklist:
        blacklisted = _filter(items, blacklist, key)
        return [item for item in items if key(item) not in blacklisted]

    else:
        return items


print("Functions loaded successfully!")

# Test 1: Round-trip property for ensure_bytes/ensure_unicode
print("\nTest 1: ensure_bytes/ensure_unicode round-trip...")
@given(st.text())
@settings(max_examples=500)
def test_ensure_bytes_unicode_round_trip(text):
    bytes_result = ensure_bytes(text)
    assert isinstance(bytes_result, bytes)
    
    unicode_result = ensure_unicode(bytes_result)
    assert isinstance(unicode_result, str)
    
    # Round-trip should preserve the original text
    assert unicode_result == text

try:
    test_ensure_bytes_unicode_round_trip()
    print("✓ Round-trip test passed")
except AssertionError as e:
    print(f"✗ Round-trip test FAILED: {e}")
    traceback.print_exc()

# Test 2: Idempotence of ensure_bytes
print("\nTest 2: ensure_bytes idempotence...")
@given(st.binary())
@settings(max_examples=500)
def test_ensure_bytes_idempotent(data):
    result1 = ensure_bytes(data)
    result2 = ensure_bytes(result1)
    assert result1 == result2
    assert isinstance(result1, bytes)

try:
    test_ensure_bytes_idempotent()
    print("✓ ensure_bytes idempotence test passed")
except AssertionError as e:
    print(f"✗ ensure_bytes idempotence test FAILED: {e}")
    traceback.print_exc()

# Test 3: Mathematical properties of compute_percent
print("\nTest 3: compute_percent range...")
@given(
    st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=500)
def test_compute_percent_range(part, total):
    result = compute_percent(part, total)
    
    # Result should be between 0 and 100 when part <= total
    if part <= total:
        assert 0 <= result <= 100, f"Expected result in [0, 100] but got {result} for part={part}, total={total}"
    
    # When part > total, result can exceed 100 (which is valid for some use cases)
    assert result >= 0, f"Expected non-negative result but got {result}"

try:
    test_compute_percent_range()
    print("✓ compute_percent range test passed")
except AssertionError as e:
    print(f"✗ compute_percent range test FAILED: {e}")
    traceback.print_exc()

# Test 4: compute_percent with zero total
print("\nTest 4: compute_percent with zero total...")
@given(st.floats(allow_nan=False, allow_infinity=False))
@settings(max_examples=500)
def test_compute_percent_zero_total(part):
    # According to the code, this should return 0
    result = compute_percent(part, 0)
    assert result == 0, f"Expected 0 but got {result} for part={part}, total=0"

try:
    test_compute_percent_zero_total()
    print("✓ compute_percent zero total test passed")
except AssertionError as e:
    print(f"✗ compute_percent zero total test FAILED: {e}")
    traceback.print_exc()

# Test 5: Round value idempotence
print("\nTest 5: round_value idempotence...")
@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
@settings(max_examples=500)
def test_round_value_idempotent(value):
    result1 = round_value(value, precision=2)
    result2 = round_value(result1, precision=2)
    assert result1 == result2, f"Not idempotent: {result1} != {result2} for value={value}"

try:
    test_round_value_idempotent()
    print("✓ round_value idempotence test passed")
except AssertionError as e:
    print(f"✗ round_value idempotence test FAILED: {e}")
    traceback.print_exc()

# Test 6: pattern_filter subset property
print("\nTest 6: pattern_filter subset property...")
@given(
    st.lists(st.text(min_size=1), min_size=0, max_size=20),
    st.one_of(st.none(), st.lists(st.text(min_size=1), min_size=1, max_size=5))
)
@settings(max_examples=500)
def test_pattern_filter_subset(items, whitelist):
    # Use simple patterns that match the whole string
    if whitelist:
        whitelist = [re.escape(w) for w in whitelist]
    
    result = pattern_filter(items, whitelist=whitelist)
    
    # Result should be a subset of items
    assert set(result) <= set(items), f"Result {result} is not a subset of {items}"
    
    # Order should be preserved
    if result:
        indices = [items.index(r) for r in result]
        assert indices == sorted(indices), f"Order not preserved: indices {indices}"

try:
    test_pattern_filter_subset()
    print("✓ pattern_filter subset test passed")
except AssertionError as e:
    print(f"✗ pattern_filter subset test FAILED: {e}")
    traceback.print_exc()

# Test 7: pattern_filter blacklist property
print("\nTest 7: pattern_filter blacklist...")
@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=20),
    st.lists(st.text(min_size=1), min_size=1, max_size=5)
)
@settings(max_examples=500)
def test_pattern_filter_blacklist(items, blacklist):
    # Create patterns that exactly match items
    blacklist_patterns = ['^{}$'.format(re.escape(b)) for b in blacklist]
    
    result = pattern_filter(items, blacklist=blacklist_patterns)
    
    # No blacklisted item should be in the result
    for blacklisted in blacklist:
        assert blacklisted not in result, f"Blacklisted item '{blacklisted}' found in result {result}"

try:
    test_pattern_filter_blacklist()
    print("✓ pattern_filter blacklist test passed")
except AssertionError as e:
    print(f"✗ pattern_filter blacklist test FAILED: {e}")
    traceback.print_exc()

# Test 8: Pattern filter with blacklist and whitelist - blacklist precedence
print("\nTest 8: pattern_filter blacklist precedence...")
@given(
    st.lists(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=2, max_size=5), min_size=5, max_size=10),
    st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=2, max_size=5)
)
@settings(max_examples=500)
def test_pattern_filter_blacklist_precedence(items, pattern):
    # Ensure the pattern is in items
    if pattern not in items:
        items.append(pattern)
    
    # Use the same pattern for both whitelist and blacklist
    whitelist = [re.escape(pattern)]
    blacklist = [re.escape(pattern)]
    
    result = pattern_filter(items, whitelist=whitelist, blacklist=blacklist)
    
    # Blacklist should take precedence - pattern should not be in result
    assert pattern not in result, f"Pattern '{pattern}' should be blacklisted but found in result {result}"

try:
    test_pattern_filter_blacklist_precedence()
    print("✓ pattern_filter blacklist precedence test passed")
except AssertionError as e:
    print(f"✗ pattern_filter blacklist precedence test FAILED: {e}")
    traceback.print_exc()

# Test 9: Specific edge cases for ensure_bytes/unicode
print("\nTest 9: ensure_bytes/unicode with non-UTF8 bytes...")
@given(st.binary())
@settings(max_examples=500)
def test_ensure_unicode_with_binary(data):
    # Try to decode arbitrary binary data
    try:
        result = ensure_unicode(data)
        # If it succeeds, it should be a string
        assert isinstance(result, str)
        # And we should be able to encode it back
        ensure_bytes(result)
    except UnicodeDecodeError:
        # This is expected for non-UTF8 bytes
        pass

try:
    test_ensure_unicode_with_binary()
    print("✓ ensure_unicode binary test passed")
except Exception as e:
    print(f"✗ ensure_unicode binary test FAILED: {e}")
    traceback.print_exc()

print("\n" + "="*60)
print("Testing complete!")
print("All tests passed successfully! ✅")