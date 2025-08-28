#!/usr/bin/env python3
import troposphere.refactorspaces as refactorspaces
import inspect

# Get the source of the boolean function
try:
    source = inspect.getsource(refactorspaces.boolean)
    print("=== Source code of boolean function ===")
    print(source)
except:
    print("Could not get source")

# Get the module for boolean
print(f"\n=== Boolean function details ===")
print(f"Module: {refactorspaces.boolean.__module__}")
print(f"Doc: {refactorspaces.boolean.__doc__}")

# Test more cases
print("\n=== Extended boolean tests ===")
test_cases = [
    (True, "Python True"),
    (False, "Python False"), 
    (1, "Integer 1"),
    (0, "Integer 0"),
    ("true", "String 'true'"),
    ("false", "String 'false'"),
    ("True", "String 'True'"),
    ("False", "String 'False'"),
    ("TRUE", "String 'TRUE'"),
    ("FALSE", "String 'FALSE'"),
    ("Yes", "String 'Yes'"),
    ("No", "String 'No'"),
    ("1", "String '1'"),
    ("0", "String '0'"),
    (None, "None"),
    ("", "Empty string"),
    ([1], "Non-empty list"),
    ([], "Empty list"),
    ({}, "Empty dict"),
    ({"a": 1}, "Non-empty dict"),
    (2, "Integer 2"),
    (-1, "Integer -1"),
    (0.0, "Float 0.0"),
    (1.0, "Float 1.0"),
    ("random", "Random string"),
]

for value, description in test_cases:
    try:
        result = refactorspaces.boolean(value)
        print(f"  boolean({repr(value):20}) = {result:5} # {description}")
    except Exception as e:
        error_msg = str(e) if str(e) else "Raised exception with no message"
        print(f"  boolean({repr(value):20}) RAISED: {error_msg} # {description}")