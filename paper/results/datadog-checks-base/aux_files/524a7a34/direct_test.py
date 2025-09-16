#!/usr/bin/env python3
"""Direct test of datadog_checks functions"""

import sys
import os
import re
import math
import traceback

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/datadog-checks-base_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings

# Try direct import from specific files
import importlib.util

def load_module_from_file(name, file_path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load the utils/common module directly
common_path = '/root/hypothesis-llm/envs/datadog-checks-base_env/lib/python3.13/site-packages/datadog_checks/base/utils/common.py'
common = load_module_from_file('common', common_path)

ensure_bytes = common.ensure_bytes
ensure_unicode = common.ensure_unicode
compute_percent = common.compute_percent
round_value = common.round_value
pattern_filter = common.pattern_filter

print("Loaded functions successfully!")

# Test 1: Round-trip property for ensure_bytes/ensure_unicode
print("\nTesting ensure_bytes/ensure_unicode round-trip...")
@given(st.text())
@settings(max_examples=100)
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
    print(f"✗ Round-trip test failed: {e}")
    traceback.print_exc()

# Test 2: Idempotence of ensure_bytes
print("\nTesting ensure_bytes idempotence...")
@given(st.binary())
@settings(max_examples=100)
def test_ensure_bytes_idempotent(data):
    result1 = ensure_bytes(data)
    result2 = ensure_bytes(result1)
    assert result1 == result2
    assert isinstance(result1, bytes)

try:
    test_ensure_bytes_idempotent()
    print("✓ ensure_bytes idempotence test passed")
except AssertionError as e:
    print(f"✗ ensure_bytes idempotence test failed: {e}")
    traceback.print_exc()

# Test 3: Mathematical properties of compute_percent
print("\nTesting compute_percent...")
@given(
    st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_compute_percent_range(part, total):
    result = compute_percent(part, total)
    
    # Result should be between 0 and 100 when part <= total
    if part <= total:
        assert 0 <= result <= 100
    
    # When part > total, result can exceed 100 (which is valid for some use cases)
    assert result >= 0

try:
    test_compute_percent_range()
    print("✓ compute_percent range test passed")
except AssertionError as e:
    print(f"✗ compute_percent range test failed: {e}")
    traceback.print_exc()

# Test 4: compute_percent with zero total
print("\nTesting compute_percent with zero total...")
@given(st.floats(allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_compute_percent_zero_total(part):
    # According to the code, this should return 0
    assert compute_percent(part, 0) == 0

try:
    test_compute_percent_zero_total()
    print("✓ compute_percent zero total test passed")
except AssertionError as e:
    print(f"✗ compute_percent zero total test failed: {e}")
    traceback.print_exc()

# Test 5: Round value idempotence
print("\nTesting round_value idempotence...")
@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_round_value_idempotent(value):
    result1 = round_value(value, precision=2)
    result2 = round_value(result1, precision=2)
    assert result1 == result2

try:
    test_round_value_idempotent()
    print("✓ round_value idempotence test passed")
except AssertionError as e:
    print(f"✗ round_value idempotence test failed: {e}")
    traceback.print_exc()

# Test 6: pattern_filter subset property
print("\nTesting pattern_filter subset property...")
@given(
    st.lists(st.text(min_size=1), min_size=0, max_size=10),
    st.one_of(st.none(), st.lists(st.text(min_size=1), min_size=1, max_size=3))
)
@settings(max_examples=100)
def test_pattern_filter_subset(items, whitelist):
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

try:
    test_pattern_filter_subset()
    print("✓ pattern_filter subset test passed")
except AssertionError as e:
    print(f"✗ pattern_filter subset test failed: {e}")
    traceback.print_exc()

# Test 7: pattern_filter blacklist property
print("\nTesting pattern_filter blacklist...")
@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=10),
    st.lists(st.text(min_size=1), min_size=1, max_size=3)
)
@settings(max_examples=100)
def test_pattern_filter_blacklist(items, blacklist):
    # Create patterns that exactly match items
    blacklist_patterns = ['^{}$'.format(re.escape(b)) for b in blacklist]
    
    result = pattern_filter(items, blacklist=blacklist_patterns)
    
    # No blacklisted item should be in the result
    for blacklisted in blacklist:
        assert blacklisted not in result

try:
    test_pattern_filter_blacklist()
    print("✓ pattern_filter blacklist test passed")
except AssertionError as e:
    print(f"✗ pattern_filter blacklist test failed: {e}")
    traceback.print_exc()

# Test 8: Pattern filter with blacklist and whitelist
print("\nTesting pattern_filter blacklist precedence...")
@given(
    st.lists(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=2, max_size=5), min_size=5, max_size=10),
    st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=2, max_size=5)
)
@settings(max_examples=100)
def test_pattern_filter_blacklist_precedence(items, pattern):
    # Ensure the pattern is in items
    if pattern not in items:
        items.append(pattern)
    
    # Use the same pattern for both whitelist and blacklist
    whitelist = [re.escape(pattern)]
    blacklist = [re.escape(pattern)]
    
    result = pattern_filter(items, whitelist=whitelist, blacklist=blacklist)
    
    # Blacklist should take precedence - pattern should not be in result
    assert pattern not in result

try:
    test_pattern_filter_blacklist_precedence()
    print("✓ pattern_filter blacklist precedence test passed")
except AssertionError as e:
    print(f"✗ pattern_filter blacklist precedence test failed: {e}")
    traceback.print_exc()

print("\n" + "="*60)
print("Testing complete!")