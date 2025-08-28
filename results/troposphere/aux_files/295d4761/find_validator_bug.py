#!/usr/bin/env python3
"""
Find bugs in troposphere validators by testing edge cases
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# First, let's look at the actual boolean validator implementation
print("Boolean validator implementation check:")
print("="*50)

import troposphere.validators as validators
import inspect

print("Source of boolean function:")
print(inspect.getsource(validators.boolean))

# Now test it
print("\nTesting boolean validator:")
print("="*50)

# According to the source, it checks:
# if x in [True, 1, "1", "true", "True"]: return True
# if x in [False, 0, "0", "false", "False"]: return False
# else: raise ValueError

# Let's test the exact values it claims to support
valid_true = [True, 1, "1", "true", "True"]
valid_false = [False, 0, "0", "false", "False"]

print("Testing documented True values:")
for val in valid_true:
    result = validators.boolean(val)
    print(f"  boolean({val!r}) = {result}")
    assert result is True

print("\nTesting documented False values:")
for val in valid_false:
    result = validators.boolean(val)
    print(f"  boolean({val!r}) = {result}")
    assert result is False

# Now test edge cases that should fail but might not
print("\nTesting edge cases that SHOULD raise ValueError:")

edge_cases = [
    2,           # Integer other than 0 or 1
    -1,          # Negative integer
    1.0,         # Float equal to 1
    0.0,         # Float equal to 0
    "TRUE",      # All caps (not in list)
    "FALSE",     # All caps (not in list)
    "yes",       # Common boolean string
    "no",        # Common boolean string
    "",          # Empty string
    None,        # None
    [],          # Empty list
    [True],      # List with boolean
]

for val in edge_cases:
    try:
        result = validators.boolean(val)
        print(f"  BUG? boolean({val!r}) = {result} (should have raised ValueError)")
    except ValueError:
        print(f"  OK: boolean({val!r}) raised ValueError")
    except Exception as e:
        print(f"  UNEXPECTED: boolean({val!r}) raised {type(e).__name__}: {e}")

print("\n" + "="*50)
print("Integer validator implementation check:")
print(inspect.getsource(validators.integer))

print("\nTesting integer validator:")
print("="*50)

# The integer validator tries int(x) and catches ValueError/TypeError
# Let's test what Python's int() actually accepts

test_values = [
    # (value, should_pass, description)
    (1, True, "integer"),
    ("123", True, "numeric string"),
    ("-456", True, "negative numeric string"),
    (1.0, True, "float 1.0"),
    (2.0, True, "float 2.0"),
    (1.5, False, "non-integer float"),
    ("1.0", False, "string float"),
    ("1.5", False, "string non-integer float"),
    (True, True, "boolean True (equals 1)"),
    (False, True, "boolean False (equals 0)"),
    ("", False, "empty string"),
    ("abc", False, "non-numeric string"),
    (None, False, "None"),
    ([], False, "empty list"),
]

for val, should_pass, desc in test_values:
    try:
        result = validators.integer(val)
        if should_pass:
            print(f"  OK: integer({val!r}) = {result} ({desc})")
        else:
            print(f"  BUG: integer({val!r}) = {result} - should have failed ({desc})")
            # Double-check Python's int() behavior
            try:
                int_val = int(val)
                print(f"    Note: int({val!r}) = {int_val}")
            except:
                print(f"    Note: int({val!r}) raises exception")
    except ValueError as e:
        if not should_pass:
            print(f"  OK: integer({val!r}) raised ValueError ({desc})")
        else:
            print(f"  BUG: integer({val!r}) raised ValueError - should have passed ({desc})")
            # Double-check Python's int() behavior
            try:
                int_val = int(val)
                print(f"    Note: int({val!r}) = {int_val}")
            except:
                print(f"    Note: int({val!r}) raises exception")

print("\n" + "="*50)
print("Double validator implementation check:")
print(inspect.getsource(validators.double))

print("\nTesting double validator:")
print("="*50)

# The double validator tries float(x) and catches ValueError/TypeError
test_doubles = [
    # (value, should_pass, description)
    (1, True, "integer"),
    (1.5, True, "float"),
    ("123", True, "numeric string"),
    ("1.5", True, "float string"),
    ("1e10", True, "scientific notation"),
    ("-2.5e-3", True, "negative scientific"),
    (True, True, "boolean True"),
    (False, True, "boolean False"),
    ("", False, "empty string"),
    ("abc", False, "non-numeric string"),
    (None, False, "None"),
    ([], False, "empty list"),
    (float('inf'), True, "infinity"),
    (float('nan'), True, "NaN"),
]

for val, should_pass, desc in test_doubles:
    try:
        result = validators.double(val)
        if should_pass:
            print(f"  OK: double({val!r}) = {result} ({desc})")
        else:
            print(f"  BUG: double({val!r}) = {result} - should have failed ({desc})")
    except ValueError as e:
        if not should_pass:
            print(f"  OK: double({val!r}) raised ValueError ({desc})")
        else:
            print(f"  BUG: double({val!r}) raised ValueError - should have passed ({desc})")