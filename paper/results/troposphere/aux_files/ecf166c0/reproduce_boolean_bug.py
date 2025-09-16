"""
Minimal reproduction of the boolean() function bug in troposphere.datazone
"""

import troposphere.datazone as dz

# The bug: boolean() accepts float values 0.0 and 1.0
print("Bug demonstration:")
print(f"dz.boolean(0.0) = {dz.boolean(0.0)}")  # Returns False, should raise ValueError
print(f"dz.boolean(1.0) = {dz.boolean(1.0)}")  # Returns True, should raise ValueError

# Why this happens:
print("\nRoot cause analysis:")
print(f"0.0 in [0, False] = {0.0 in [0, False]}")  # True (because 0.0 == 0)
print(f"1.0 in [1, True] = {1.0 in [1, True]}")    # True (because 1.0 == 1)

# This violates the function's intended behavior of only accepting
# specific types: bool, int (0 or 1), and strings ("0", "1", "true", "false", etc.)