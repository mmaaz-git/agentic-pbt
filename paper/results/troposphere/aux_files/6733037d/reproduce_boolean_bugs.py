#!/usr/bin/env python3
import troposphere.refactorspaces as refactorspaces

print("=== Bug 1: ValueError with no error message ===")
try:
    # This will raise ValueError with no message
    result = refactorspaces.boolean("")
except ValueError as e:
    error_msg = str(e)
    print(f"ValueError raised with message: '{error_msg}'")
    print(f"Is message empty? {error_msg == ''}")

print("\n=== Bug 2: Case sensitivity inconsistency ===")
test_cases = ["true", "True", "TRUE", "false", "False", "FALSE"]
for test in test_cases:
    try:
        result = refactorspaces.boolean(test)
        print(f"boolean('{test}') = {result}")
    except ValueError:
        print(f"boolean('{test}') raised ValueError")