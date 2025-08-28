"""Minimal reproduction of the float handling issue in troposphere.entityresolution.boolean"""

import troposphere.entityresolution as er

# The function accepts float 0.0 and 1.0 unexpectedly
print("Testing float values with boolean():")

# These work but probably shouldn't (floats)
print(f"boolean(0.0) = {er.boolean(0.0)}")  # Returns False
print(f"boolean(1.0) = {er.boolean(1.0)}")  # Returns True
print(f"boolean(-0.0) = {er.boolean(-0.0)}")  # Returns False

# These raise ValueError as expected
try:
    er.boolean(2.0)
except ValueError:
    print("boolean(2.0) raises ValueError (expected)")

try:
    er.boolean(0.5)
except ValueError:
    print("boolean(0.5) raises ValueError (expected)")

# The issue: The function uses 'in' operator with a list containing integers
# Python's behavior: 0.0 == 0 and 1.0 == 1, so 0.0 in [0] is True
print("\nWhy this happens:")
print(f"0.0 in [0] = {0.0 in [0]}")  # True
print(f"1.0 in [1] = {1.0 in [1]}")  # True
print(f"2.0 in [2] = {2.0 in [2]}")  # True (but 2 is not in the accepted list)