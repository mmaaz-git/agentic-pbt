#!/usr/bin/env python3
"""Minimal reproducer for Bug 1: Boolean validator accepts float values."""

from troposphere import validators

# The boolean validator should only accept these values:
# [True, False, 1, 0, '1', '0', 'true', 'false', 'True', 'False']

# But it incorrectly accepts float values:
print("validators.boolean(0.0) =", validators.boolean(0.0))  # Returns False
print("validators.boolean(1.0) =", validators.boolean(1.0))  # Returns True

# This happens because Python's 'in' operator uses == equality:
print("\n0.0 in [0] =", 0.0 in [0])  # True
print("1.0 in [1] =", 1.0 in [1])  # True

# The validator source code is:
# def boolean(x: Any) -> bool:
#     if x in [True, 1, "1", "true", "True"]:
#         return True
#     if x in [False, 0, "0", "false", "False"]:
#         return False
#     raise ValueError

print("\nThis violates the documented contract that only specific values are accepted.")
print("Float values should raise ValueError like other invalid inputs.")