import inspect
import troposphere

# Get the module file location
print(f"Module location: {troposphere.__file__}")

# Get all public functions and classes
members = inspect.getmembers(troposphere, lambda x: not str(x).startswith('_'))

# Filter classes and functions
classes = []
functions = []
for name, obj in members:
    if inspect.isclass(obj):
        classes.append(name)
    elif inspect.isfunction(obj):
        functions.append(name)

print(f"\nClasses ({len(classes)}):")
for cls in classes[:10]:  # First 10
    print(f"  - {cls}")
if len(classes) > 10:
    print(f"  ... and {len(classes) - 10} more")

print(f"\nFunctions ({len(functions)}):")
for func in functions[:10]:  # First 10
    print(f"  - {func}")
if len(functions) > 10:
    print(f"  ... and {len(functions) - 10} more")

# Look at the main __init__ file structure
print("\n\nChecking main module structure...")
print(f"Module docstring: {troposphere.__doc__[:200] if troposphere.__doc__ else 'None'}...")