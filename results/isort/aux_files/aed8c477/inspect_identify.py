import inspect
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.identify

# Get all public members
members = inspect.getmembers(isort.identify)
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

# Print public functions and classes
print("Public functions and classes in isort.identify:")
for name, obj in public_members:
    if inspect.isfunction(obj) or inspect.isclass(obj):
        print(f'\n{name}: {type(obj).__name__}')
        if hasattr(obj, '__doc__'):
            doc = obj.__doc__
            if doc:
                print(f'  Doc: {doc.strip()[:200]}')
        
        # Get function signature if it's a function
        if inspect.isfunction(obj):
            try:
                sig = inspect.signature(obj)
                print(f'  Signature: {sig}')
            except:
                pass

# Let's also see the Import class attributes
print("\n\nImport class structure:")
print(f"  Fields: {isort.identify.Import._fields}")
print(f"  Defaults: {isort.identify.Import._field_defaults}")