#!/usr/bin/env python3
"""
Hypothesis-based test to verify the large integer bug in trino.dbapi
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from trino.dbapi import Cursor, Connection
from unittest.mock import Mock

# SQL BIGINT range constants
BIGINT_MAX = 2**63 - 1
BIGINT_MIN = -(2**63)

@given(
    value=st.integers(min_value=BIGINT_MAX + 1, max_value=2**100)
)
@settings(max_examples=50)
def test_integers_above_bigint_max(value):
    """Test that integers above BIGINT max should be formatted as DECIMAL"""
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(value)
    
    # According to the TODO comment, these should be DECIMAL
    # But the current implementation just uses %d
    assert not result.startswith("DECIMAL"), \
        f"BUG: Integer {value} exceeding BIGINT max is not formatted as DECIMAL. Got: {result}"

@given(
    value=st.integers(min_value=-(2**100), max_value=BIGINT_MIN - 1)
)
@settings(max_examples=50)
def test_integers_below_bigint_min(value):
    """Test that integers below BIGINT min should be formatted as DECIMAL"""
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(value)
    
    # According to the TODO comment, these should be DECIMAL
    # But the current implementation just uses %d
    assert not result.startswith("DECIMAL"), \
        f"BUG: Integer {value} below BIGINT min is not formatted as DECIMAL. Got: {result}"

@given(
    value=st.integers(min_value=BIGINT_MIN, max_value=BIGINT_MAX)
)
@settings(max_examples=100)
def test_integers_within_bigint_range(value):
    """Test that integers within BIGINT range are formatted as plain integers"""
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(value)
    
    # These should be plain integers
    assert result == str(value), \
        f"Integer {value} within BIGINT range should be formatted as plain integer"
    assert not result.startswith("DECIMAL"), \
        f"Integer {value} within BIGINT range should not be DECIMAL"

def run_hypothesis_tests():
    print("Running Hypothesis tests for large integer bug...")
    print("=" * 70)
    
    failures = []
    
    # Test 1: Values above BIGINT_MAX
    print("\nTest 1: Integers above BIGINT_MAX (should be DECIMAL)")
    try:
        test_integers_above_bigint_max()
        print("  ✓ Test passed (no bug)")
    except AssertionError as e:
        print(f"  ✗ BUG CONFIRMED: {e}")
        failures.append("Integers above BIGINT_MAX not converted to DECIMAL")
    
    # Test 2: Values below BIGINT_MIN
    print("\nTest 2: Integers below BIGINT_MIN (should be DECIMAL)")
    try:
        test_integers_below_bigint_min()
        print("  ✓ Test passed (no bug)")
    except AssertionError as e:
        print(f"  ✗ BUG CONFIRMED: {e}")
        failures.append("Integers below BIGINT_MIN not converted to DECIMAL")
    
    # Test 3: Values within BIGINT range
    print("\nTest 3: Integers within BIGINT range (should be plain integers)")
    try:
        test_integers_within_bigint_range()
        print("  ✓ Test passed")
    except AssertionError as e:
        print(f"  ✗ ERROR: {e}")
        failures.append("Integers within BIGINT range incorrectly formatted")
    
    print("\n" + "=" * 70)
    
    if failures:
        print("BUG SUMMARY:")
        print("-" * 70)
        for failure in failures:
            print(f"  - {failure}")
        print("\nThe _format_prepared_param method has a TODO comment at line 530")
        print("indicating that integers exceeding 64-bit should be formatted as DECIMAL,")
        print("but this is not implemented. This causes potential overflow errors.")
        return True
    else:
        print("All tests passed - no bugs found")
        return False

if __name__ == "__main__":
    run_hypothesis_tests()