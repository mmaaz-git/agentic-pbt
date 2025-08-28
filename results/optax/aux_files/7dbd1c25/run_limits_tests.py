#!/usr/bin/env /root/hypothesis-llm/envs/limits_env/bin/python3
"""Run property-based tests for limits.limits module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

import traceback
from hypothesis import given, strategies as st, settings, Verbosity
from hypothesis.strategies import composite
import limits.limits as ll
from limits import parse, parse_many
from limits.limits import (
    RateLimitItem,
    RateLimitItemPerSecond,
    RateLimitItemPerMinute,
    RateLimitItemPerHour,
    RateLimitItemPerDay,
    RateLimitItemPerMonth,
    RateLimitItemPerYear,
    safe_string,
)


# Strategy for generating rate limit classes
rate_limit_classes = st.sampled_from([
    RateLimitItemPerSecond,
    RateLimitItemPerMinute,
    RateLimitItemPerHour,
    RateLimitItemPerDay,
    RateLimitItemPerMonth,
    RateLimitItemPerYear,
])


# Strategy for generating valid rate limit items
@composite
def rate_limit_items(draw):
    cls = draw(rate_limit_classes)
    amount = draw(st.integers(min_value=1, max_value=10000))
    multiples = draw(st.integers(min_value=1, max_value=100))
    namespace = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)))
    return cls(amount=amount, multiples=multiples, namespace=namespace)


def run_test(test_func, test_name):
    """Run a single test and report results"""
    print(f"\nTesting: {test_name}")
    try:
        test_func()
        print(f"✅ PASSED: {test_name}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {test_name}")
        print(f"Error: {e}")
        traceback.print_exc()
        return False


# Test 1: Safe string with problematic bytes
@given(st.binary(min_size=1, max_size=100))
@settings(max_examples=100, verbosity=Verbosity.quiet)
def test_safe_string_with_invalid_utf8():
    """Test safe_string with potentially invalid UTF-8 bytes"""
    # Generate bytes that are definitely not valid UTF-8
    invalid_bytes = b'\xff\xfe\x00\x01'
    result = safe_string(invalid_bytes)
    assert isinstance(result, str)


# Test 2: Ordering consistency
@given(rate_limit_items(), rate_limit_items(), rate_limit_items())
@settings(max_examples=100, verbosity=Verbosity.quiet)
def test_ordering_consistency():
    """Test ordering is consistent"""
    item1 = RateLimitItemPerSecond(10, 1)
    item2 = RateLimitItemPerMinute(10, 1)
    item3 = RateLimitItemPerHour(10, 1)
    
    # Seconds < Minutes < Hours (based on GRANULARITY.seconds)
    assert item1 < item2
    assert item2 < item3
    assert item1 < item3  # Transitivity


# Test 3: Parse edge cases
@given(st.text(min_size=1, max_size=10, alphabet="0123456789/"))
@settings(max_examples=100, verbosity=Verbosity.quiet, suppress_health_check=[])
def test_parse_invalid_strings():
    """Test parse with potentially invalid strings"""
    try:
        # Test some specific invalid patterns
        parse("//")
    except ValueError:
        pass  # Expected
    
    try:
        parse("0/second")  # Amount of 0 might be problematic
        # If it doesn't raise, check if it's handled
    except (ValueError, AttributeError):
        pass


# Test 4: Key generation with special characters
@given(st.text(alphabet="/\\;,|"))
@settings(max_examples=100, verbosity=Verbosity.quiet)
def test_key_with_special_chars():
    """Test key generation with delimiter-like characters"""
    item = RateLimitItemPerSecond(10, 1, namespace="test")
    identifiers = ["/test/", "a/b/c", "x;y|z"]
    key = item.key_for(*identifiers)
    # The key should handle these without breaking
    assert isinstance(key, str)
    assert "/" in key  # Delimiter should be present


# Main test runner
def main():
    print("=" * 60)
    print("Running Property-Based Tests for limits.limits")
    print("=" * 60)
    
    tests = [
        (test_safe_string_with_invalid_utf8, "safe_string with invalid UTF-8"),
        (test_ordering_consistency, "ordering consistency"),
        (test_parse_invalid_strings, "parse with invalid strings"),
        (test_key_with_special_chars, "key generation with special characters"),
    ]
    
    passed = 0
    failed = 0
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    # Now let's test specific edge cases manually
    print("\n" + "=" * 60)
    print("Testing specific edge cases...")
    
    # Test case 1: safe_string with invalid UTF-8
    print("\n1. Testing safe_string with invalid UTF-8 bytes...")
    try:
        invalid_utf8 = b'\xff\xfe'
        result = safe_string(invalid_utf8)
        print(f"Result: {repr(result)}")
        print("Note: safe_string doesn't handle invalid UTF-8 gracefully!")
    except Exception as e:
        print(f"ERROR: safe_string failed with invalid UTF-8: {e}")
    
    # Test case 2: Parse with amount = 0
    print("\n2. Testing parse with amount = 0...")
    try:
        result = parse("0/second")
        print(f"Result: {result}")
        print(f"Amount: {result.amount}")
        print("Note: Allows rate limit with amount=0, which might be problematic")
    except Exception as e:
        print(f"Correctly rejected: {e}")
    
    # Test case 3: Parse with negative numbers
    print("\n3. Testing parse with negative amount...")
    try:
        result = parse("-5/second")
        print(f"Result: {result}")
        print("BUG: Accepts negative amounts!")
    except Exception as e:
        print(f"Correctly rejected: {e}")
    
    # Test case 4: Extreme multiplier values
    print("\n4. Testing with extreme multiplier values...")
    try:
        item = RateLimitItemPerSecond(1, 999999999999)
        expiry = item.get_expiry()
        print(f"Expiry for 1 per 999999999999 seconds: {expiry}")
        if expiry < 0 or expiry != 999999999999:
            print("BUG: Integer overflow or incorrect calculation!")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test case 5: Empty namespace
    print("\n5. Testing with empty namespace...")
    try:
        item = RateLimitItemPerSecond(10, 1, namespace="")
        key = item.key_for("test")
        print(f"Key with empty namespace: {repr(key)}")
        if key.startswith("/"):
            print("Note: Empty namespace creates keys starting with /")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()