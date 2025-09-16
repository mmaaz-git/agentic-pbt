import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import inspect
import coremltools.converters as converters

# Get module information
print("Module path:", converters.__file__)
print("\nModule structure:\n")

# Get all public members
members = inspect.getmembers(converters, lambda member: not member.__name__.startswith('_') if hasattr(member, '__name__') else True)

for name, obj in members[:30]:  # First 30 items
    obj_type = type(obj).__name__
    print(f"  {name}: {obj_type}")