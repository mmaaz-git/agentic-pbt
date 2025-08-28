#!/usr/bin/env python3
"""
Minimal reproduction of boolean validator accepting float values.
This demonstrates a discrepancy between type hints and implementation.
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# According to type hints, these should not be accepted
print("Testing boolean validator with float inputs:")
print(f"boolean(1.0) = {boolean(1.0)}")  # Returns True
print(f"boolean(0.0) = {boolean(0.0)}")  # Returns False
print(f"boolean(-0.0) = {boolean(-0.0)}")  # Returns False

# This happens because Python's 'in' operator uses equality
print("\nWhy this happens:")
print(f"1.0 in [1] = {1.0 in [1]}")  # True
print(f"0.0 in [0] = {0.0 in [0]}")  # True

# Type hints claim only these are accepted:
print("\nType hints claim to accept only:")
print("  True, False, 1, 0, 'true', 'false', 'True', 'False', '1', '0'")
print("\nBut implementation also accepts:")
print("  1.0, 0.0, -0.0 (any float equal to 0 or 1)")