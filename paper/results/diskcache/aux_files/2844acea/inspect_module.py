import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')
import jurigged.runpy
import inspect

print('Functions in module:')
for name, obj in inspect.getmembers(jurigged.runpy):
    if inspect.isfunction(obj):
        try:
            sig = inspect.signature(obj)
            print(f'  - {name}: {sig}')
        except:
            print(f'  - {name}: (no signature)')
    elif inspect.isclass(obj):
        print(f'  - {name} (class)')

print('\nPublic functions (no underscore):')
for name in dir(jurigged.runpy):
    if not name.startswith('_'):
        obj = getattr(jurigged.runpy, name)
        if callable(obj):
            try:
                sig = inspect.signature(obj)
                doc = (obj.__doc__ or '').split('\n')[0][:60]
                print(f'  - {name}{sig}: {doc}')
            except:
                print(f'  - {name}: (callable)')