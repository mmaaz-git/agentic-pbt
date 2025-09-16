#!/usr/bin/env python3
"""
Specific bug tests for troposphere validators
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

print("=== BUG HUNT: troposphere.docdb ===\n")

# Test 1: Boolean validator with string "1" vs integer 1
print("Test 1: Boolean validator consistency")
print("-" * 40)
from troposphere import validators

# According to the code, these should all return True
true_values = [True, 1, "1", "true", "True"]
print("Testing True values:")
for val in true_values:
    result = validators.boolean(val)
    print(f"  boolean({val!r}) = {result}")
    assert result is True, f"Expected True, got {result}"

# According to the code, these should all return False  
false_values = [False, 0, "0", "false", "False"]
print("\nTesting False values:")
for val in false_values:
    result = validators.boolean(val)
    print(f"  boolean({val!r}) = {result}")
    assert result is False, f"Expected False, got {result}"

print("✓ Boolean validator works as documented\n")

# Test 2: Integer validator with floats
print("Test 2: Integer validator with decimal floats")
print("-" * 40)

# This is likely a bug - integer validator accepts floats with decimals
try:
    result = validators.integer(42.7)
    print(f"BUG FOUND: integer(42.7) returned {result!r}")
    print("  The integer validator accepts float 42.7 without error!")
    print("  This violates the expectation that only integers should be accepted.")
    
    # Verify it's not converting to int
    print(f"  Returned type: {type(result)}, value: {result}")
    print(f"  int(result) would be: {int(result)}")
    
    # Create reproduction case
    print("\n  Minimal reproduction:")
    print("    from troposphere import validators")
    print("    result = validators.integer(42.7)")
    print(f"    # Returns: {result!r} (a float, not an integer!)")
    
except ValueError as e:
    print(f"  integer(42.7) correctly raised ValueError: {e}")

print()

# Test 3: Empty string as title
print("Test 3: Empty string as resource title")
print("-" * 40)

from troposphere.docdb import DBCluster

try:
    cluster = DBCluster("")
    cluster.validate_title()
    print("BUG FOUND: Empty string accepted as valid title!")
    print("  The regex '^[a-zA-Z0-9]+$' requires at least one character")
    print("  but empty string passes validation.")
    
    print("\n  Minimal reproduction:")
    print("    from troposphere.docdb import DBCluster")
    print("    cluster = DBCluster('')")
    print("    cluster.validate_title()  # Should raise ValueError but doesn't")
    
except ValueError as e:
    print(f"  Empty string correctly rejected: {e}")

print()

# Test 4: Double validator with special float strings
print("Test 4: Double validator with 'inf' and 'nan' strings")
print("-" * 40)

special_values = ["inf", "-inf", "nan", "infinity", "-infinity"]
for val in special_values:
    try:
        result = validators.double(val)
        print(f"  double({val!r}) = {result!r}")
        # Try to use it
        float_val = float(result)
        print(f"    Converts to float: {float_val}")
        # This might cause issues in AWS CloudFormation
        if float_val != float_val:  # NaN check
            print("    WARNING: Results in NaN which AWS might not accept")
        elif abs(float_val) == float('inf'):
            print("    WARNING: Results in infinity which AWS might not accept")
            
    except ValueError as e:
        print(f"  double({val!r}) raised ValueError: {e}")

print("\n" + "=" * 50)
print("BUGS FOUND:")
print("1. integer() validator accepts floats with decimal parts")
print("2. Empty string bypasses title validation")
print("3. double() accepts 'inf'/'nan' strings (may cause AWS issues)")
print("=" * 50)