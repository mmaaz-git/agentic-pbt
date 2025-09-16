import inspect
import InquirerPy

# Get module file location
print(f"Module location: {InquirerPy.__file__}")

# Get all public members
members = inspect.getmembers(InquirerPy, lambda x: not inspect.ismodule(x))
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

print("\nPublic members in InquirerPy:")
for name, obj in public_members:
    obj_type = type(obj).__name__
    print(f"  {name}: {obj_type}")
    if callable(obj) and hasattr(obj, '__doc__') and obj.__doc__:
        doc_first_line = obj.__doc__.split('\n')[0].strip()
        if doc_first_line:
            print(f"    -> {doc_first_line[:100]}")

# Also check for submodules
import os
module_dir = os.path.dirname(InquirerPy.__file__)
print(f"\nSubmodules in {module_dir}:")
for item in os.listdir(module_dir):
    if item.endswith('.py') and not item.startswith('_'):
        print(f"  {item}")
    elif os.path.isdir(os.path.join(module_dir, item)) and not item.startswith('_'):
        print(f"  {item}/")