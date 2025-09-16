import inspect
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.mediatailor as mediatailor

# Get all public classes/functions
classes = inspect.getmembers(mediatailor, lambda m: inspect.isclass(m) and not m.__name__.startswith('_'))
print('Public classes in troposphere.mediatailor:')
for name, cls in classes:
    print(f'  {name}')
    # Check if it has props attribute
    if hasattr(cls, 'props'):
        print(f'    Has props: {list(cls.props.keys())[:3]}...' if len(cls.props) > 3 else f'    Has props: {list(cls.props.keys())}')
    
# Check if there are any functions
functions = inspect.getmembers(mediatailor, inspect.isfunction)
public_functions = [f for f in functions if not f[0].startswith('_')]
print(f'\nPublic functions: {len(public_functions)}')
if public_functions:
    for name, func in public_functions[:5]:
        print(f'  {name}: {inspect.signature(func)}')

# Check parent classes
print('\nLet\'s look at base classes:')
from troposphere import AWSObject, AWSProperty
print(f'AWSObject: {AWSObject.__module__}.{AWSObject.__name__}')
print(f'AWSProperty: {AWSProperty.__module__}.{AWSProperty.__name__}')

# Check if any classes have interesting methods
print('\nClass methods to test:')
for name, cls in classes[:3]:
    methods = [m for m in dir(cls) if not m.startswith('_') and callable(getattr(cls, m))]
    print(f'{name}: {methods[:5]}')