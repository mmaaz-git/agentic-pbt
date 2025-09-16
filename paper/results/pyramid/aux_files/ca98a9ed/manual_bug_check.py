#!/usr/bin/env python3
"""Manual bug checking for pyramid.events"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.events import BeforeRender

print("Manual Bug Check for pyramid.events")
print("=" * 60)

# Potential Bug 1: BeforeRender with 'rendering_val' key in system dict
print("\n1. Testing BeforeRender with 'rendering_val' key conflict:")
print("-" * 40)

system_dict = {'rendering_val': 'dict_value', 'other_key': 'other_value'}
rendering_val_param = {'param': 'value'}

event = BeforeRender(system_dict, rendering_val_param)

print(f"system_dict: {system_dict}")
print(f"rendering_val parameter: {rendering_val_param}")
print(f"event.rendering_val (attribute): {event.rendering_val}")
print(f"event['rendering_val'] (dict key): {event.get('rendering_val', 'KEY NOT FOUND')}")

# Check if there's a conflict
if event.rendering_val != event.get('rendering_val'):
    print("✗ POTENTIAL BUG: Attribute and dict key have different values!")
    print("  This could be confusing as the same name refers to different values")
    print("  depending on access method (attribute vs dict key)")

# Potential Bug 2: BeforeRender mutates the original dict
print("\n2. Testing BeforeRender mutation behavior:")
print("-" * 40)

original = {'key1': 'value1', 'key2': 'value2'}
original_copy = original.copy()
event = BeforeRender(original)

# Modify through the event
event['new_key'] = 'new_value'
event['key1'] = 'modified_value'

print(f"Original dict before: {original_copy}")
print(f"Original dict after: {original}")
print(f"Event dict: {dict(event)}")

if original != original_copy:
    print("✗ POTENTIAL BUG: BeforeRender modifies the original system dict!")
    print("  This violates the principle of least surprise")
    print("  Users might not expect their original dict to be modified")

# Potential Bug 3: Check dict initialization behavior
print("\n3. Testing dict initialization behavior:")
print("-" * 40)

# BeforeRender inherits from dict, let's see how it initializes
test_dict = {'a': 1, 'b': 2}
event = BeforeRender(test_dict)

# Since BeforeRender inherits from dict and calls dict.__init__(self, system)
# Let's verify this works correctly
print(f"Test dict: {test_dict}")
print(f"Event dict (via dict()): {dict(event)}")
print(f"Event keys: {list(event.keys())}")
print(f"Are they equal? {dict(event) == test_dict}")

# Potential Bug 4: Testing special dict methods
print("\n4. Testing special dict methods:")
print("-" * 40)

event = BeforeRender({'a': 1, 'b': 2}, rendering_val="test")

# Test update method
event.update({'c': 3, 'd': 4})
print(f"After update: {dict(event)}")

# Test setdefault
result = event.setdefault('e', 5)
print(f"setdefault('e', 5) returned: {result}")
print(f"Dict now: {dict(event)}")

# Test pop with rendering_val
event['rendering_val'] = 'dict_value'
print(f"Before pop - event['rendering_val']: {event.get('rendering_val')}")
print(f"Before pop - event.rendering_val: {event.rendering_val}")

popped = event.pop('rendering_val', None)
print(f"Popped value: {popped}")
print(f"After pop - event.get('rendering_val'): {event.get('rendering_val')}")
print(f"After pop - event.rendering_val: {event.rendering_val}")

if event.rendering_val is not None and 'rendering_val' not in event:
    print("✗ POTENTIAL BUG: Attribute rendering_val persists even after dict key is removed!")

# Summary
print("\n" + "=" * 60)
print("Analysis complete. Check output above for potential bugs.")