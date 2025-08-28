import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import inspect
import troposphere.location

print("=== Module Members ===")
members = inspect.getmembers(troposphere.location)
for name, obj in members:
    if not name.startswith('_'):
        obj_type = type(obj).__name__
        print(f"{name}: {obj_type}")

print("\n=== Classes and Functions ===")
for name, obj in members:
    if not name.startswith('_'):
        if inspect.isclass(obj):
            print(f"\nClass: {name}")
            print(f"  Docstring: {obj.__doc__}")
            # Get methods
            methods = inspect.getmembers(obj, predicate=inspect.ismethod)
            for method_name, method in methods:
                if not method_name.startswith('_'):
                    print(f"  Method: {method_name}")
        elif inspect.isfunction(obj):
            print(f"\nFunction: {name}")
            print(f"  Signature: {inspect.signature(obj)}")
            print(f"  Docstring: {obj.__doc__}")