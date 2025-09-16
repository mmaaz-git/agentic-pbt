#!/usr/bin/env python3
"""Comprehensive property-based tests for parse_vars to find bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, example, note
from pyramid.scripts.common import parse_vars
import string

# More targeted strategies based on understanding typical usage
ascii_key = st.text(
    alphabet=string.ascii_letters + string.digits + "_-.",
    min_size=1,
    max_size=50
)

# Keys that might be problematic
edge_key = st.one_of(
    st.just(""),  # Empty key
    st.text(min_size=1, max_size=1),  # Single char
    st.text(alphabet=string.whitespace, min_size=1, max_size=10),  # Only whitespace
    st.text(alphabet="🦄🎉😀", min_size=1, max_size=5),  # Unicode
    st.text(alphabet="\n\r\t", min_size=1, max_size=5),  # Control chars
    st.text(alphabet=string.punctuation.replace("=", ""), min_size=1, max_size=10),  # Punctuation
)

# Any text without equals for keys
any_key = st.text(min_size=0, max_size=100).filter(lambda x: "=" not in x)

# Values can be anything
any_value = st.text(min_size=0, max_size=200)

# Run and capture results
def test_property(name, test_func):
    print(f"\n{name}")
    print("-" * 40)
    
    @settings(max_examples=200, deadline=None)
    def wrapper():
        test_func()
    
    try:
        wrapper()
        print("✓ PASS: No bugs found")
        return True
    except AssertionError as e:
        print(f"✗ BUG FOUND: {e}")
        return False
    except Exception as e:
        print(f"✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

print("=" * 60)
print("COMPREHENSIVE PROPERTY-BASED TESTING FOR parse_vars")
print("=" * 60)

# Test 1: Stress test with edge case keys
@given(edge_key, any_value)
@example("", "value")  # Empty key
@example(" ", "value")  # Space key
@example("\t", "value")  # Tab key
@example("\n", "value")  # Newline key
@example("🦄", "🎉")  # Unicode
def test_edge_case_keys(key, value):
    """Test parse_vars with unusual keys."""
    note(f"Testing key={repr(key)}, value={repr(value)}")
    
    input_str = f"{key}={value}"
    result = parse_vars([input_str])
    
    assert len(result) == 1, f"Expected 1 item, got {len(result)}"
    assert key in result, f"Key {repr(key)} not in result"
    assert result[key] == value, f"Value mismatch: expected {repr(value)}, got {repr(result[key])}"

test_property("Test 1: Edge case keys", test_edge_case_keys)

# Test 2: Multiple equals signs at boundaries
@given(any_key)
@example("")  # Empty key with just equals
@example("=")  # Key that is equals... wait this would have equals in it
def test_boundary_equals(key):
    """Test with equals at value boundaries."""
    test_cases = [
        f"{key}==",  # Value starts with equals
        f"{key}===",  # Multiple equals at start
        f"{key}=a=",  # Equals at end
        f"{key}==a",  # Equals at start
        f"{key}====",  # All equals value
    ]
    
    for input_str in test_cases:
        note(f"Testing: {repr(input_str)}")
        result = parse_vars([input_str])
        # After first equals, everything is value
        expected_value = input_str[len(key)+1:]
        assert result[key] == expected_value

test_property("Test 2: Boundary equals signs", test_boundary_equals)

# Test 3: Order and overwriting behavior
@given(st.lists(st.tuples(any_key, any_value), min_size=2, max_size=10))
def test_overwriting_behavior(pairs):
    """Test that later values overwrite earlier ones for same key."""
    # Create a list with some duplicate keys
    if len(pairs) > 1:
        # Force at least one duplicate
        pairs[1] = (pairs[0][0], pairs[1][1])
    
    input_list = [f"{k}={v}" for k, v in pairs]
    result = parse_vars(input_list)
    
    # Build expected result - later values should win
    expected = {}
    for k, v in pairs:
        expected[k] = v
    
    assert result == expected

test_property("Test 3: Overwriting behavior", test_overwriting_behavior)

# Test 4: Large inputs
@given(st.dictionaries(
    ascii_key,
    st.text(min_size=0, max_size=10000),  # Large values
    min_size=1,
    max_size=100  # Many items
))
def test_large_inputs(d):
    """Test with large values and many items."""
    input_list = [f"{k}={v}" for k, v in d.items()]
    result = parse_vars(input_list)
    assert result == d

test_property("Test 4: Large inputs", test_large_inputs)

# Test 5: Unicode stress test
@given(
    st.text(alphabet=st.characters(blacklist_categories=['Cc'], blacklist_characters='='), min_size=1, max_size=50),
    st.text(alphabet=st.characters(blacklist_categories=['Cc']), min_size=0, max_size=100)
)
def test_unicode_stress(key, value):
    """Test with various Unicode characters."""
    note(f"Unicode test: key={repr(key)}, value={repr(value)}")
    
    input_str = f"{key}={value}"
    result = parse_vars([input_str])
    
    assert result == {key: value}

test_property("Test 5: Unicode stress test", test_unicode_stress)

# Test 6: Null bytes and control characters
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: "=" not in x),
    st.text(min_size=0, max_size=100)
)
@example("key", "\x00")  # Null byte in value
@example("\x01", "value")  # Control char in key
@example("key", "val\x00ue")  # Null in middle
def test_control_characters(key, value):
    """Test with control characters including null bytes."""
    note(f"Control char test: key={repr(key)}, value={repr(value)}")
    
    input_str = f"{key}={value}"
    result = parse_vars([input_str])
    
    assert result == {key: value}

test_property("Test 6: Control characters", test_control_characters)

# Test 7: Whitespace handling
@given(
    st.text(alphabet=string.whitespace, min_size=1, max_size=10),
    st.text(alphabet=string.whitespace, min_size=0, max_size=10)
)
def test_whitespace_only(key, value):
    """Test with only whitespace characters."""
    assume("=" not in key)  # Filter out equals in key
    
    input_str = f"{key}={value}"
    result = parse_vars([input_str])
    
    assert result == {key: value}

test_property("Test 7: Whitespace-only strings", test_whitespace_only)

# Test 8: Special case - single equals
def test_single_equals():
    """Test the edge case of just '='."""
    result = parse_vars(["="])
    assert result == {"": ""}, f"Expected empty key and value, got {result}"
    print("\n✓ Single equals '=' correctly parsed as empty key and value")

test_single_equals()

# Test 9: Interaction with special strings
special_strings = [
    "key=__proto__",  # Prototype pollution attempt
    "__proto__=value",
    "constructor=value",
    "key=${value}",  # Shell-like substitution
    "key=$(command)",  # Command substitution attempt
    "key=`command`",  # Backtick command
    "key=%s",  # Format string
    "key=%(name)s",  # Python format string
]

def test_special_strings():
    """Test potentially dangerous string patterns."""
    print("\nTest 9: Special string patterns")
    print("-" * 40)
    
    for input_str in special_strings:
        try:
            result = parse_vars([input_str])
            key, value = input_str.split("=", 1)
            assert result == {key: value}, f"Failed for {input_str}"
            print(f"✓ {input_str} -> {result}")
        except Exception as e:
            print(f"✗ Failed on {input_str}: {e}")
            return False
    
    print("✓ All special strings handled safely")
    return True

test_special_strings()

print("\n" + "=" * 60)
print("TESTING COMPLETE")
print("=" * 60)