import troposphere.rds as rds
import inspect

# Get all classes in the module
classes = []
for name, obj in inspect.getmembers(rds):
    if inspect.isclass(obj) and obj.__module__.startswith('troposphere'):
        classes.append((name, obj))

print(f"Found {len(classes)} classes in troposphere.rds")
print("\nClasses with their docstrings:")
for name, cls in classes[:10]:  # Show first 10
    print(f"\n{name}:")
    doc = cls.__doc__ or "No docstring"
    print(f"  {doc[:200] if len(doc) > 200 else doc}")
    
    # Show a few attributes
    attrs = [a for a in dir(cls) if not a.startswith('_') and not callable(getattr(cls, a, None))][:5]
    if attrs:
        print(f"  Attributes: {attrs}")