#!/usr/bin/env python3
"""Hypothesis-based property tests that demonstrate bugs in limits.limits"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, example
from limits.limits import safe_string
from limits import parse

# Property test that reveals the bug
@given(st.binary(min_size=1, max_size=10))
@example(b'\xff\xfe')  # Specific example that will fail
@example(b'\x80\x81')  # Another invalid UTF-8 sequence
@example(b'\xc0\xc1')  # More invalid UTF-8
@settings(max_examples=50)
def test_safe_string_handles_all_bytes(byte_value):
    """
    Property: safe_string should handle ANY bytes input without crashing
    According to its docstring, it should "normalize a byte/str/int or float to a str"
    """
    try:
        result = safe_string(byte_value)
        assert isinstance(result, str), "Result should always be a string"
        print(f"✓ Handled {repr(byte_value)[:30]}...")
    except UnicodeDecodeError as e:
        print(f"\n❌ BUG FOUND: safe_string crashes on {repr(byte_value)}")
        print(f"   Error: {e}")
        raise AssertionError(f"safe_string crashed with UnicodeDecodeError on bytes: {repr(byte_value)}")

# Test for zero/negative amounts
@given(st.integers(min_value=-100, max_value=0))
@settings(max_examples=10)
def test_parse_non_positive_amounts(amount):
    """
    Property: Rate limits should reject non-positive amounts
    """
    try:
        limit_string = f"{amount}/second"
        result = parse(limit_string)
        if amount <= 0:
            print(f"\n⚠️  ISSUE: Accepted non-positive amount: {amount}")
            print(f"   Result: {result}")
    except ValueError:
        pass  # This is expected for non-positive amounts

# Run the tests
if __name__ == "__main__":
    print("=" * 70)
    print("HYPOTHESIS PROPERTY-BASED TESTING FOR limits.limits")
    print("=" * 70)
    
    print("\n### Test 1: safe_string property test")
    print("Property: safe_string should handle ANY bytes without crashing\n")
    
    try:
        test_safe_string_handles_all_bytes()
        print("\nAll tests passed!")
    except AssertionError as e:
        print(f"\n{e}")
        print("\nThis is a genuine bug - safe_string crashes on non-UTF-8 bytes")
    
    print("\n" + "-" * 70)
    print("\n### Test 2: parse with non-positive amounts")
    test_parse_non_positive_amounts()
    
    print("\n" + "=" * 70)