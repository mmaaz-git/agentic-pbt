import inspect
import Cython.Utils as Utils

print("Cython.Utils functions with signatures:")
for name, obj in inspect.getmembers(Utils):
    if not name.startswith('_') and inspect.isfunction(obj):
        print(f"\n{name}:")
        try:
            sig = inspect.signature(obj)
            print(f"  Signature: {sig}")
        except (ValueError, TypeError):
            print("  Signature: (unavailable)")
        
        if hasattr(obj, '__doc__') and obj.__doc__:
            print(f"  Docstring: {obj.__doc__.strip()[:200]}")
        
        # Try to get source if possible
        try:
            source_file = inspect.getfile(obj)
            print(f"  Source file: {source_file}")
        except:
            pass