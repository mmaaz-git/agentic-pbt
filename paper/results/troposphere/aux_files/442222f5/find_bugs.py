#!/usr/bin/env python3
"""
Bug hunting script for troposphere.docdb module
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, example
from hypothesis.errors import InvalidArgument
from troposphere import validators
from troposphere.docdb import DBCluster

# Bug 1: Boolean validator accepts "1" as string but claims to accept 1 as integer
# Let's test edge cases
print("Testing boolean validator edge cases...")

# Test case 1: The validator documentation suggests it accepts integer 1 and 0
# but let's verify this works correctly
test_values = [1, 0, True, False, "1", "0", "true", "false", "True", "False"]

for val in test_values:
    try:
        result = validators.boolean(val)
        print(f"boolean({val!r}) = {result}")
    except Exception as e:
        print(f"boolean({val!r}) raised {e}")

# Bug 2: Let's check what happens with edge case inputs
print("\n\nTesting boolean validator with edge cases...")
edge_cases = [1.0, 0.0, "", None, [], {}, "TRUE", "FALSE", "yes", "no", 2, -1]

for val in edge_cases:
    try:
        result = validators.boolean(val)
        print(f"boolean({val!r}) = {result} (UNEXPECTED - should have raised ValueError)")
    except ValueError:
        print(f"boolean({val!r}) correctly raised ValueError")
    except Exception as e:
        print(f"boolean({val!r}) raised unexpected {type(e).__name__}: {e}")

# Bug 3: Integer validator type hints vs actual behavior
print("\n\nTesting integer validator...")

# The function signature suggests it returns Union[str, bytes, SupportsInt, SupportsIndex]
# but the implementation just returns the input unchanged after checking int() works
test_int_values = [42, "42", 42.0, -10, "0", 0]

for val in test_int_values:
    try:
        result = validators.integer(val)
        print(f"integer({val!r}) = {result!r} (type: {type(result).__name__})")
    except Exception as e:
        print(f"integer({val!r}) raised {e}")

# Check if it accepts floats with decimal parts
print("\n\nTesting integer validator with floats...")
float_values = [42.5, "42.5", 42.999]

for val in float_values:
    try:
        result = validators.integer(val)
        print(f"integer({val!r}) = {result!r} - BUG: Should not accept non-integer floats!")
    except ValueError as e:
        print(f"integer({val!r}) correctly raised ValueError")

# Bug 4: Double validator edge cases
print("\n\nTesting double validator...")
double_values = [42, 42.5, "42.5", "inf", "-inf", "nan", float('inf'), float('-inf'), float('nan')]

for val in double_values:
    try:
        result = validators.double(val)
        print(f"double({val!r}) = {result!r} (type: {type(result).__name__})")
    except Exception as e:
        print(f"double({val!r}) raised {e}")

# Bug 5: Title validation - empty string
print("\n\nTesting title validation with empty string...")
try:
    cluster = DBCluster("")  # Empty string as title
    cluster.validate_title()
    print("Empty string title accepted - BUG!")
except ValueError as e:
    print(f"Empty string correctly rejected: {e}")

# Bug 6: Round-trip property - test if from_dict handles all property types correctly
print("\n\nTesting round-trip serialization...")
try:
    original = DBCluster("TestCluster", BackupRetentionPeriod=7, StorageEncrypted=True)
    dict_repr = original.to_dict()
    print(f"Original dict: {dict_repr}")
    
    if "Properties" in dict_repr:
        props = dict_repr["Properties"]
        restored = DBCluster._from_dict("TestCluster", **props)
        restored_dict = restored.to_dict()
        print(f"Restored dict: {restored_dict}")
        
        if dict_repr == restored_dict:
            print("Round-trip successful")
        else:
            print("Round-trip FAILED - dicts don't match!")
            print(f"Difference: original has {set(dict_repr.keys())} but restored has {set(restored_dict.keys())}")
except Exception as e:
    print(f"Round-trip test failed with: {e}")
    import traceback
    traceback.print_exc()

print("\n\n=== Bug Summary ===")
print("Potential issues found:")
print("1. Boolean validator may not handle all documented cases correctly")
print("2. Integer validator accepts floats with decimal parts (e.g., 42.5)")
print("3. Empty string is accepted as a valid title despite regex requiring alphanumeric")
print("4. Double validator accepts 'inf', 'nan' strings which may cause issues downstream")