#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.interfaces as pi
from zope.interface import Interface

# Get all attributes of the module
all_items = dir(pi)

# Filter for Interface classes
interfaces = []
for name in all_items:
    obj = getattr(pi, name)
    # Check if it's a subclass of Interface
    try:
        if isinstance(obj, type) and issubclass(obj, Interface):
            interfaces.append((name, obj))
    except:
        pass

print(f"Found {len(interfaces)} interfaces in pyramid.interfaces:")
for name, obj in interfaces[:20]:  # Show first 20
    print(f"  - {name}")
    
# Check for constants and special values
constants = []
for name in all_items:
    if name.isupper() or name.startswith('PHASE'):
        constants.append(name)
        
if constants:
    print(f"\nFound {len(constants)} constants:")
    for name in constants:
        val = getattr(pi, name)
        print(f"  - {name} = {repr(val)}")

# Check for any concrete implementations with callable methods
print("\nChecking for testable concrete implementations...")
for name in all_items:
    if not name.startswith('_'):
        obj = getattr(pi, name)
        if hasattr(obj, '__dict__') and not isinstance(obj, type):
            print(f"  Found object: {name} of type {type(obj)}")