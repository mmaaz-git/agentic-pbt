import requests.hooks
import inspect

print('File location:', requests.hooks.__file__)
print('\nModule contents:')
for name, obj in inspect.getmembers(requests.hooks):
    if not name.startswith('_'):
        print(f'  {name}: {type(obj).__name__}')
        
print('\nPublic functions:')
for name, obj in inspect.getmembers(requests.hooks):
    if not name.startswith('_') and callable(obj):
        print(f'\n{name}:')
        print(f'  Signature: {inspect.signature(obj) if hasattr(obj, "__call__") else "N/A"}')
        doc = obj.__doc__
        if doc:
            print(f'  Docstring: {doc.strip()[:200]}...' if len(doc.strip()) > 200 else f'  Docstring: {doc.strip()}')