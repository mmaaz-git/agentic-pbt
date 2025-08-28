#!/usr/bin/env python3
"""
Focused test demonstrating the float bug in boolean validator
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
from troposphere.validators import boolean


@given(st.floats())
def test_boolean_validator_float_behavior(value):
    """Test that the boolean validator handles floats incorrectly"""
    if value == 0.0 or value == 1.0:
        # These float values are incorrectly accepted
        result = boolean(value)
        if value == 0.0:
            assert result is False
        else:
            assert result is True
        print(f"Float {value} incorrectly accepted and converted to {result}")
    else:
        # Other floats should raise ValueError
        try:
            result = boolean(value)
            # If we get here, it's likely another edge case
            if value == int(value) and int(value) in [0, 1]:
                # Another float that equals 0 or 1
                print(f"Float {value} incorrectly accepted (equals {int(value)})")
        except ValueError:
            pass  # Expected


# Demonstrate the bug directly
def demonstrate_bug():
    print("Demonstrating boolean validator float bug:")
    print("=" * 50)
    
    # These should raise ValueError but don't
    test_cases = [0.0, 1.0, -0.0, 1.00000]
    
    for value in test_cases:
        try:
            result = boolean(value)
            print(f"BUG: boolean({value}) = {result} (type: {type(value).__name__})")
            print(f"     Expected: ValueError")
            print(f"     Actual: {result}")
            print()
        except ValueError:
            print(f"OK: boolean({value}) correctly raised ValueError")
    
    # Show that integers are accepted (as documented)
    print("\nFor comparison, integers are correctly handled:")
    for value in [0, 1]:
        result = boolean(value)
        print(f"OK: boolean({value}) = {result} (type: {type(value).__name__})")
    
    print("\nStrings are also correctly handled:")
    for value in ["0", "1", "true", "false"]:
        result = boolean(value)
        print(f"OK: boolean('{value}') = {result}")
    
    # Test equality that causes the bug
    print("\n" + "=" * 50)
    print("Root cause analysis:")
    print(f"0.0 == 0: {0.0 == 0}")
    print(f"1.0 == 1: {1.0 == 1}")
    print(f"0.0 in [0]: {0.0 in [0]}")
    print(f"1.0 in [1]: {1.0 in [1]}")
    print("\nThe 'in' operator uses == for comparison, causing floats to match integers")


if __name__ == "__main__":
    demonstrate_bug()
    print("\n" + "=" * 50)
    print("Running property-based test...")
    test_boolean_validator_float_behavior()