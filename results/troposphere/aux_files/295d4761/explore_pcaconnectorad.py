#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere.pcaconnectorad as pcaconnectorad

# Get module file location
print(f"Module file: {pcaconnectorad.__file__}")

# Get all public members
members = inspect.getmembers(pcaconnectorad, lambda x: not inspect.ismodule(x))
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

print(f"\nTotal public members: {len(public_members)}")

# Categorize members
classes = []
functions = []
other = []

for name, obj in public_members:
    if inspect.isclass(obj):
        classes.append((name, obj))
    elif inspect.isfunction(obj):
        functions.append((name, obj))
    else:
        other.append((name, obj))

print(f"\nClasses: {len(classes)}")
for name, cls in classes[:10]:  # Show first 10
    print(f"  - {name}")
    if hasattr(cls, '__doc__') and cls.__doc__:
        print(f"    Doc: {cls.__doc__[:100]}...")

print(f"\nFunctions: {len(functions)}")
for name, func in functions:
    print(f"  - {name}")
    
print(f"\nOther: {len(other)}")
for name, obj in other[:5]:
    print(f"  - {name}: {type(obj).__name__}")