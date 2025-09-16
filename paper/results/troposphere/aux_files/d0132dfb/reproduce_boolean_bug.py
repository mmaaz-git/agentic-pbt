#!/usr/bin/env python3
"""
Minimal reproduction of the boolean validator bug in troposphere.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test valid values
print("Testing valid values:")
print(f"boolean(True) = {boolean(True)}")
print(f"boolean(False) = {boolean(False)}")
print(f"boolean(1) = {boolean(1)}")
print(f"boolean(0) = {boolean(0)}")

# Test invalid value that raises bare ValueError
print("\nTesting invalid value:")
try:
    result = boolean(-1)
    print(f"boolean(-1) = {result}")
except ValueError as e:
    print(f"ValueError raised with message: '{e}'")
    print(f"Exception args: {e.args}")
    print("BUG: The ValueError has no message, making debugging difficult!")