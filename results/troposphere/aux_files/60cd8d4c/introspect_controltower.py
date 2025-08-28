import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere.controltower as ct

# Get all public members
members = inspect.getmembers(ct)
print('Public members in troposphere.controltower:')
for name, obj in members:
    if not name.startswith('_'):
        print(f'- {name}: {type(obj).__name__}')

print('\n=== Classes ===')
for name, obj in members:
    if inspect.isclass(obj) and not name.startswith('_'):
        print(f'\nClass: {name}')
        print(f'  MRO: {[c.__name__ for c in obj.__mro__]}')
        if hasattr(obj, 'props'):
            print(f'  Properties: {obj.props}')
        # Check if it has methods
        methods = [m for m in dir(obj) if not m.startswith('_') and callable(getattr(obj, m))]
        if methods:
            print(f'  Methods: {methods}')
        
print('\n=== Imported types ===')
print('AWSObject base class:', ct.AWSObject)
print('AWSProperty base class:', ct.AWSProperty)

# Let's also check the parent module
import troposphere
print('\n=== Base classes from troposphere ===')
print('AWSObject methods:', [m for m in dir(troposphere.AWSObject) if not m.startswith('_')])
print('AWSProperty methods:', [m for m in dir(troposphere.AWSProperty) if not m.startswith('_')])