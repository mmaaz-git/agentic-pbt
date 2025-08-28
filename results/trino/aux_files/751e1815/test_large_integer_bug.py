#!/usr/bin/env python3
"""
Test to demonstrate the large integer bug in trino.dbapi
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from trino.dbapi import Cursor, Connection
from unittest.mock import Mock

def test_large_integer_bug():
    print("Testing Large Integer Formatting Bug in trino.dbapi")
    print("=" * 70)
    
    # Setup
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    # SQL BIGINT range is -2^63 to 2^63-1
    BIGINT_MAX = 2**63 - 1
    BIGINT_MIN = -(2**63)
    
    print("\nSQL BIGINT limits:")
    print(f"  Maximum: {BIGINT_MAX} (2^63 - 1)")
    print(f"  Minimum: {BIGINT_MIN} (-2^63)")
    
    print("\n" + "-" * 70)
    print("Testing values within BIGINT range:")
    
    # Test values within range
    test_values_ok = [
        (0, "Zero"),
        (1, "One"),
        (-1, "Negative one"),
        (BIGINT_MAX, "BIGINT MAX"),
        (BIGINT_MIN, "BIGINT MIN"),
    ]
    
    for value, desc in test_values_ok:
        result = cursor._format_prepared_param(value)
        print(f"  {desc}: {value}")
        print(f"    Formatted as: {result}")
        assert result == str(value), f"Expected {value}, got {result}"
    
    print("\n" + "-" * 70)
    print("Testing values EXCEEDING BIGINT range:")
    print("(These should be converted to DECIMAL according to TODO comment)")
    
    # Test values exceeding range
    test_values_overflow = [
        (BIGINT_MAX + 1, "BIGINT_MAX + 1"),
        (BIGINT_MIN - 1, "BIGINT_MIN - 1"),
        (2**64, "2^64"),
        (2**100, "2^100 (very large)"),
        (10**30, "10^30 (scientific notation)"),
    ]
    
    bug_confirmed = False
    
    for value, desc in test_values_overflow:
        result = cursor._format_prepared_param(value)
        print(f"\n  {desc}: {value}")
        print(f"    Formatted as: {result}")
        
        # Check if it's formatted as DECIMAL
        if result.startswith("DECIMAL"):
            print(f"    ✓ Correctly formatted as DECIMAL")
        else:
            print(f"    ✗ BUG: Formatted as plain integer, not DECIMAL!")
            print(f"    This will cause overflow in database!")
            bug_confirmed = True
    
    print("\n" + "=" * 70)
    
    if bug_confirmed:
        print("BUG CONFIRMED: Large integers are not converted to DECIMAL")
        print("\nDetails:")
        print("- Location: dbapi.py line 530-531")
        print("- TODO comment says: 'represent numbers exceeding 64-bit (BIGINT) as DECIMAL'")
        print("- Current behavior: All integers formatted with '%d' regardless of size")
        print("- Impact: Integer overflow errors when values exceed BIGINT range")
        print("\nExample failing case:")
        print(f"  Value: {2**63} (2^63)")
        print(f"  Current output: {cursor._format_prepared_param(2**63)}")
        print(f"  Expected output: DECIMAL '{2**63}'")
        return True
    else:
        print("No bug found - large integers are properly handled")
        return False

if __name__ == "__main__":
    bug_found = test_large_integer_bug()
    
    if bug_found:
        print("\n" + "=" * 70)
        print("SUGGESTED FIX:")
        print("-" * 70)
        print("Replace lines 529-531 in dbapi.py:")
        print()
        print("Current code:")
        print("    if isinstance(param, int):")
        print("        # TODO represent numbers exceeding 64-bit (BIGINT) as DECIMAL")
        print("        return \"%d\" % param")
        print()
        print("Fixed code:")
        print("    if isinstance(param, int):")
        print("        # Check if integer exceeds BIGINT range")
        print("        if param < -(2**63) or param > (2**63 - 1):")
        print("            return \"DECIMAL '%d'\" % param")
        print("        return \"%d\" % param")
        print("=" * 70)