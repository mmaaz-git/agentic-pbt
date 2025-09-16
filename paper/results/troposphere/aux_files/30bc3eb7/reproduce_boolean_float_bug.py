"""Minimal reproduction for boolean validator accepting floats"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

# Test float 0.0 and 1.0
print("Testing boolean validator with floats:")
print(f"boolean(0.0) = {validators.boolean(0.0)}")  # Expected to raise ValueError, but returns False
print(f"boolean(1.0) = {validators.boolean(1.0)}")  # Expected to raise ValueError, but returns True

# Test other float values
try:
    result = validators.boolean(0.5)
    print(f"boolean(0.5) = {result}")
except ValueError as e:
    print(f"boolean(0.5) raised ValueError: {e}")

try:
    result = validators.boolean(2.0)
    print(f"boolean(2.0) = {result}")
except ValueError as e:
    print(f"boolean(2.0) raised ValueError: {e}")

# Check the cause - Python's == comparison
print("\nPython equality checks:")
print(f"0.0 == 0: {0.0 == 0}")  # This is True in Python!
print(f"1.0 == 1: {1.0 == 1}")  # This is True in Python!
print(f"0.0 in [0]: {0.0 in [0]}")  # This is True in Python!
print(f"1.0 in [1]: {1.0 in [1]}")  # This is True in Python!