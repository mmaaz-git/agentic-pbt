#!/usr/bin/env python3
"""
Hypothesis tests that reveal bugs in troposphere.docdb
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, example, settings
import math

print("Running Hypothesis property-based tests to find bugs...")
print("=" * 60)

# Property 1: Integer validator should only accept values where int(x) == x
from troposphere import validators

@given(st.floats(allow_nan=False, allow_infinity=False))
@example(42.7)  # Specific failing case
@example(1.1)   # Another failing case
@settings(max_examples=100)
def test_integer_validator_property(x):
    """
    Property: integer() validator should only accept values where the 
    fractional part is zero (i.e., true integers)
    """
    try:
        result = validators.integer(x)
        # If it accepted the value, verify it's actually an integer
        if not math.isclose(x, int(x)):
            print(f"\n✗ BUG FOUND: integer({x}) accepted non-integer value")
            print(f"  Returned: {result!r}")
            print(f"  This violates the property that only integers should pass")
            return False
    except ValueError:
        # Correctly rejected non-integer
        pass
    return True

# Run the test
print("\nTest 1: Integer validator property")
print("-" * 40)
try:
    test_integer_validator_property()
    print("Property test completed")
except AssertionError:
    print("Property violation detected!")

# Property 2: Valid titles must be non-empty alphanumeric strings
from troposphere.docdb import DBCluster

@given(st.text())
@example("")  # Specific failing case
@settings(max_examples=100)
def test_title_validation_property(title):
    """
    Property: Resource titles must match regex ^[a-zA-Z0-9]+$ 
    which requires at least one alphanumeric character
    """
    import re
    pattern = re.compile(r'^[a-zA-Z0-9]+$')
    
    try:
        cluster = DBCluster(title)
        cluster.validate_title()
        
        # If validation passed, the title MUST match the pattern
        if not pattern.match(title):
            print(f"\n✗ BUG FOUND: Invalid title '{title}' passed validation")
            print(f"  Title does not match required pattern ^[a-zA-Z0-9]+$")
            if title == "":
                print("  Empty string should be rejected but was accepted")
            return False
                
    except ValueError:
        # Should only reject if pattern doesn't match
        if pattern.match(title):
            print(f"\n✗ BUG: Valid title '{title}' was rejected")
            return False
            
    return True

print("\nTest 2: Title validation property")  
print("-" * 40)
try:
    test_title_validation_property()
    print("Property test completed")
except AssertionError:
    print("Property violation detected!")

print("\n" + "=" * 60)
print("Testing complete. Check output above for any bugs found.")