#!/usr/bin/env python3
import inspect
import htmldate.extractors

# Get module info
print("Module file:", htmldate.extractors.__file__)
print("\nModule docstring:", htmldate.extractors.__doc__)

# Get all public functions/classes
print("\n\nPublic members:")
members = inspect.getmembers(htmldate.extractors)
for name, obj in members:
    if not name.startswith('_'):
        print(f"\n{name}: {type(obj).__name__}")
        if callable(obj) and not inspect.isclass(obj):
            try:
                sig = inspect.signature(obj)
                print(f"  Signature: {sig}")
            except:
                pass
            if obj.__doc__:
                print(f"  Docstring: {obj.__doc__[:200]}...")