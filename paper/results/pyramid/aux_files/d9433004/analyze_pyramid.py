#!/root/hypothesis-llm/envs/pyramid_env/bin/python3

import inspect
import os
import pyramid.httpexceptions as target_module

print("Module imported successfully!")
print(f"Module file: {target_module.__file__}")
print(f"Module directory: {os.path.dirname(target_module.__file__)}")

print("\nPublic members:")
members = inspect.getmembers(target_module, lambda m: not m.__name__.startswith('_') if hasattr(m, '__name__') else True)
for name, obj in members[:20]:
    if not name.startswith('_'):
        print(f"  {name}: {type(obj).__name__}")