"""Minimal reproduction of the bug in scipy.constants.convert_temperature"""

import scipy.constants as sc

# Test case that fails
val = 0.99999
result = sc.convert_temperature(val, 'Celsius', 'Celsius')

print(f"Input value: {val}")
print(f"Result after Celsius->Celsius conversion: {result}")
print(f"Values are equal: {result == val}")
print(f"Difference: {result - val}")

# This should be a no-op (identity function)
# Converting from a scale to itself should return the exact same value
print("\n--- More test cases ---")
test_values = [0.99999, 1.0, 100.0, -40.0, 0.0]
for test_val in test_values:
    result = sc.convert_temperature(test_val, 'Celsius', 'Celsius')
    if result != test_val:
        print(f"Failed: {test_val} -> {result}, diff = {result - test_val}")
        
# Test other scales
print("\n--- Testing other scale identities ---")
for scale in ['Kelvin', 'Fahrenheit', 'Rankine']:
    test_val = 100.0
    result = sc.convert_temperature(test_val, scale, scale)
    if result != test_val:
        print(f"Failed for {scale}: {test_val} -> {result}, diff = {result - test_val}")