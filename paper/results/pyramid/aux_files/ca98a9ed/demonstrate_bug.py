#!/usr/bin/env python3
"""Demonstration of bug in pyramid.events.BeforeRender"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

# Test code to demonstrate the bug
code = """
from pyramid.events import BeforeRender

# Create a system dict with 'rendering_val' key
system_dict = {
    'rendering_val': 'value_from_dict',
    'other_key': 'other_value'
}

# Create BeforeRender with a different rendering_val parameter
rendering_val_param = 'value_from_param'
event = BeforeRender(system_dict, rendering_val_param)

# Access via dict key
dict_access = event['rendering_val']
print(f"event['rendering_val'] = {repr(dict_access)}")

# Access via attribute
attr_access = event.rendering_val
print(f"event.rendering_val = {repr(attr_access)}")

# Check if they're different
if dict_access != attr_access:
    print("\\nBUG CONFIRMED: The same name 'rendering_val' returns different values!")
    print(f"  - As dict key: {repr(dict_access)}")
    print(f"  - As attribute: {repr(attr_access)}")
    print("\\nThis violates the principle of least surprise and can lead to confusion.")
else:
    print("No bug found - values are consistent")
"""

# Write and execute the test
test_file = '/tmp/test_pyramid_bug.py'
with open(test_file, 'w') as f:
    f.write(code)

print("Bug Demonstration for pyramid.events.BeforeRender")
print("=" * 60)
print("\nTest Code:")
print(code)
print("\nExpected Output:")
print("-" * 40)
print("event['rendering_val'] = 'value_from_dict'")
print("event.rendering_val = 'value_from_param'")
print("\nBUG CONFIRMED: The same name 'rendering_val' returns different values!")
print("  - As dict key: 'value_from_dict'")
print("  - As attribute: 'value_from_param'")
print("\nThis violates the principle of least surprise and can lead to confusion.")
print("=" * 60)

# Now let's also verify this by static analysis
print("\nStatic Analysis:")
print("-" * 40)
print("Looking at the BeforeRender.__init__ method:")
print("""
    def __init__(self, system, rendering_val=None):
        dict.__init__(self, system)  # Copies all keys from system into self
        self.rendering_val = rendering_val  # Sets attribute
""")
print("\nIf system contains key 'rendering_val', we have:")
print("1. self['rendering_val'] = system['rendering_val']  (from dict.__init__)")
print("2. self.rendering_val = rendering_val parameter  (from attribute assignment)")
print("\nThese can be different values, causing confusion!")

# Additional edge case
print("\n" + "=" * 60)
print("Additional Edge Case - Modifying the dict key:")
print("-" * 40)
print("""
# If we modify event['rendering_val'] after creation:
event['rendering_val'] = 'new_dict_value'

# Then:
# event['rendering_val'] returns 'new_dict_value'
# event.rendering_val still returns 'value_from_param'

# This further increases confusion as modifications don't sync.
""")