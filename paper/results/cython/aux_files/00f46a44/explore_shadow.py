import inspect
import Cython.Shadow as Shadow

print("Cython.Shadow module:")
print(f"Module file: {Shadow.__file__}")
print(f"Module docstring: {Shadow.__doc__}")

print("\nFunctions and classes in Shadow:")
for name, obj in inspect.getmembers(Shadow):
    if not name.startswith('_'):
        if inspect.isfunction(obj) or inspect.isclass(obj):
            print(f"\n{name}: {type(obj).__name__}")
            try:
                if inspect.isfunction(obj):
                    sig = inspect.signature(obj)
                    print(f"  Signature: {sig}")
            except (ValueError, TypeError):
                pass
            
            if hasattr(obj, '__doc__') and obj.__doc__:
                doc = obj.__doc__.strip()
                if doc:
                    print(f"  Docstring: {doc[:200]}")