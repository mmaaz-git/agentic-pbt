#!/usr/bin/env python3
"""Minimal test to discover specific bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test the boolean validator with an edge case
print("Testing boolean validator...")

# According to the code, these should work:
print(f"boolean(True) = {boolean(True)}")  # Should return True
print(f"boolean(1) = {boolean(1)}")  # Should return True  
print(f"boolean('1') = {boolean('1')}")  # Should return True
print(f"boolean('true') = {boolean('true')}")  # Should return True

# But what about these edge cases?
try:
    result = boolean("TRUE")  # All caps - not in the list!
    print(f"BUG FOUND: boolean('TRUE') = {result} (should raise ValueError)")
except ValueError:
    print("OK: boolean('TRUE') correctly raises ValueError")

try:
    result = boolean("FALSE")  # All caps - not in the list!
    print(f"BUG FOUND: boolean('FALSE') = {result} (should raise ValueError)")
except ValueError:
    print("OK: boolean('FALSE') correctly raises ValueError")

# The boolean function checks against exact strings, not case-insensitive
# Let's verify by looking at the actual implementation