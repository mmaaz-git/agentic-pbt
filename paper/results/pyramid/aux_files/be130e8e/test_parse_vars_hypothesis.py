#!/usr/bin/env python3
"""Hypothesis-based property tests for parse_vars function."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, example, assume
from pyramid.scripts.common import parse_vars
import traceback

# Test strategies
simple_text = st.text(min_size=1, max_size=50).filter(lambda x: '=' not in x and x.strip())
key_text = st.text(min_size=0, max_size=50).filter(lambda x: '=' not in x)  # Allow empty keys
value_text = st.text(min_size=0, max_size=100)  # Values can contain '='


def run_test(test_func, *args):
    """Run a single test and report results."""
    try:
        test_func(*args)
        return True, None
    except AssertionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {e}"


print("Running Hypothesis property tests for parse_vars...")
print("=" * 60)

# Test 1: Round-trip property
@given(st.dictionaries(key_text, value_text, min_size=1, max_size=10))
@settings(max_examples=100)
def test_round_trip(d):
    """Whatever we put in, we should get back out."""
    input_list = [f"{k}={v}" for k, v in d.items()]
    result = parse_vars(input_list)
    assert result == d, f"Round-trip failed: input {d}, got {result}"

print("Test 1: Round-trip property")
success, error = run_test(test_round_trip)
if success:
    print("✓ PASS: Round-trip property holds")
else:
    print(f"✗ FAIL: {error}")
print()

# Test 2: Single split property
@given(key_text, st.text())
@settings(max_examples=100)
def test_single_split(key, value):
    """parse_vars should split on first '=' only."""
    input_str = f"{key}={value}"
    result = parse_vars([input_str])
    assert len(result) == 1
    assert key in result
    assert result[key] == value

print("Test 2: Single split property")
success, error = run_test(test_single_split)
if success:
    print("✓ PASS: Splits on first '=' only")
else:
    print(f"✗ FAIL: {error}")
print()

# Test 3: No equals should raise
@given(simple_text)
@settings(max_examples=50)
def test_no_equals_raises(text):
    """Strings without '=' should raise ValueError."""
    try:
        parse_vars([text])
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert 'no "="' in str(e)

print("Test 3: No equals raises ValueError")
success, error = run_test(test_no_equals_raises)
if success:
    print("✓ PASS: Correctly raises ValueError for missing '='")
else:
    print(f"✗ FAIL: {error}")
print()

# Test 4: Empty key/value handling
@given(value_text)
@settings(max_examples=50)
@example("")  # Explicitly test empty value
def test_empty_key(value):
    """Empty keys should be allowed."""
    result = parse_vars([f"={value}"])
    assert result == {"": value}

print("Test 4: Empty key handling")
success, error = run_test(test_empty_key)
if success:
    print("✓ PASS: Empty keys handled correctly")
else:
    print(f"✗ FAIL: {error}")
print()

@given(key_text)
@settings(max_examples=50)
@example("")  # Explicitly test empty key
def test_empty_value(key):
    """Empty values should be allowed."""
    result = parse_vars([f"{key}="])
    assert result == {key: ""}

print("Test 5: Empty value handling")
success, error = run_test(test_empty_value)
if success:
    print("✓ PASS: Empty values handled correctly")
else:
    print(f"✗ FAIL: {error}")
print()

# Test 6: Multiple equals in value
@given(key_text, st.lists(value_text, min_size=2, max_size=5))
@settings(max_examples=50)
def test_multiple_equals_preserved(key, value_parts):
    """Multiple '=' in value should be preserved."""
    value = "=".join(value_parts)
    result = parse_vars([f"{key}={value}"])
    assert result == {key: value}
    # Check that equals signs are preserved
    assert result[key].count('=') == len(value_parts) - 1

print("Test 6: Multiple equals in value")
success, error = run_test(test_multiple_equals_preserved)
if success:
    print("✓ PASS: Multiple '=' in values preserved")
else:
    print(f"✗ FAIL: {error}")
print()

# Test 7: Duplicate keys
@given(key_text, value_text, value_text)
@settings(max_examples=50)
def test_duplicate_keys_last_wins(key, value1, value2):
    """With duplicate keys, last value should win."""
    assume(value1 != value2)  # Make sure values are different
    result = parse_vars([f"{key}={value1}", f"{key}={value2}"])
    assert result == {key: value2}

print("Test 7: Duplicate keys - last wins")
success, error = run_test(test_duplicate_keys_last_wins)
if success:
    print("✓ PASS: Last value wins for duplicate keys")
else:
    print(f"✗ FAIL: {error}")
print()

# Test 8: Order independence for unique keys
@given(st.lists(st.tuples(key_text, value_text), min_size=1, max_size=10, unique_by=lambda x: x[0]))
@settings(max_examples=50)
def test_order_independence(pairs):
    """Order shouldn't matter for unique keys."""
    input1 = [f"{k}={v}" for k, v in pairs]
    input2 = [f"{k}={v}" for k, v in reversed(pairs)]
    
    result1 = parse_vars(input1)
    result2 = parse_vars(input2)
    
    assert result1 == result2

print("Test 8: Order independence for unique keys")
success, error = run_test(test_order_independence)
if success:
    print("✓ PASS: Order doesn't matter for unique keys")
else:
    print(f"✗ FAIL: {error}")
print()

# Test 9: Special characters
@given(st.text())
@settings(max_examples=100)
def test_any_characters_in_value(value):
    """Any characters should work in values."""
    key = "test_key"
    result = parse_vars([f"{key}={value}"])
    assert result == {key: value}

print("Test 9: Any characters in values")
success, error = run_test(test_any_characters_in_value)
if success:
    print("✓ PASS: All characters work in values")
else:
    print(f"✗ FAIL: {error}")
print()

# Test 10: Idempotence when already parsed
@given(st.dictionaries(key_text, value_text, min_size=1, max_size=5))
@settings(max_examples=50)
def test_idempotent_parse(d):
    """Parsing already formatted strings should be idempotent."""
    # First format
    formatted = [f"{k}={v}" for k, v in d.items()]
    # Parse it
    parsed1 = parse_vars(formatted)
    # Format again
    formatted2 = [f"{k}={v}" for k, v in parsed1.items()]
    # Parse again
    parsed2 = parse_vars(formatted2)
    
    assert parsed1 == parsed2 == d

print("Test 10: Idempotent parsing")
success, error = run_test(test_idempotent_parse)
if success:
    print("✓ PASS: Parsing is idempotent")
else:
    print(f"✗ FAIL: {error}")

print("\n" + "=" * 60)
print("Property testing complete!")