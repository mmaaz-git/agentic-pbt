import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

import inspect
import jurigged.recode

# Get module information
print("Module location:", jurigged.recode.__file__)
print("\nModule docstring:", jurigged.recode.__doc__)

# Get all public members
members = inspect.getmembers(jurigged.recode)
print("\nPublic members:")
for name, obj in members:
    if not name.startswith('_'):
        obj_type = type(obj).__name__
        print(f"  {name}: {obj_type}")
        if inspect.isfunction(obj):
            sig = inspect.signature(obj)
            print(f"    Signature: {sig}")
            if obj.__doc__:
                print(f"    Docstring: {obj.__doc__[:100]}")
        elif inspect.isclass(obj):
            print(f"    Methods:", [m for m in dir(obj) if not m.startswith('_')])

# Look at specific classes
print("\n=== Recoder class ===")
print("Recoder docstring:", jurigged.recode.Recoder.__doc__)
print("Recoder methods:", [m for m in dir(jurigged.recode.Recoder) if not m.startswith('_')])