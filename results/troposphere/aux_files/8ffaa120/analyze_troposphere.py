import inspect
import troposphere.iotsitewise as iotsitewise

# Get the module file location
print(f"Module file: {iotsitewise.__file__}")

# Get all public members
members = inspect.getmembers(iotsitewise, lambda x: not x.__name__.startswith('_') if hasattr(x, '__name__') else True)
print(f"\nFound {len(members)} members in troposphere.iotsitewise")

# Filter for classes (likely AWS resources)
classes = [(name, obj) for name, obj in members if inspect.isclass(obj) and not name.startswith('_')]
print(f"\nClasses ({len(classes)}):")
for name, _ in classes[:10]:  # Show first 10
    print(f"  - {name}")
if len(classes) > 10:
    print(f"  ... and {len(classes) - 10} more")

# Check for any functions
functions = [(name, obj) for name, obj in members if inspect.isfunction(obj)]
print(f"\nFunctions ({len(functions)}):")
for name, _ in functions[:10]:
    print(f"  - {name}")