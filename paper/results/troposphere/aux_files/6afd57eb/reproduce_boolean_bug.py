#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

# Test float inputs
test_values = [0.0, 1.0, 0.5, -1.0, 3.14]

print("Testing boolean validator with float values:")
for value in test_values:
    try:
        result = validators.boolean(value)
        print(f"  validators.boolean({value}) = {result} (type: {type(result).__name__})")
    except ValueError as e:
        print(f"  validators.boolean({value}) raised ValueError: {e}")

print("\nChecking code equality:")
print(f"  0.0 == 0: {0.0 == 0}")
print(f"  1.0 == 1: {1.0 == 1}")
print(f"  0.0 == False: {0.0 == False}")
print(f"  1.0 == True: {1.0 == True}")

print("\nChecking 'in' operator behavior:")
print(f"  0.0 in [0]: {0.0 in [0]}")
print(f"  1.0 in [1]: {1.0 in [1]}")
print(f"  0.0 in [False, 0]: {0.0 in [False, 0]}")
print(f"  1.0 in [True, 1]: {1.0 in [True, 1]}")