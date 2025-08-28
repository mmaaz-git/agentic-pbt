import Cython
import pkgutil
import inspect

print('Cython submodules:')
for importer, modname, ispkg in pkgutil.iter_modules(Cython.__path__, prefix='Cython.'):
    print(f'  {modname} (package: {ispkg})')

print('\nKey Cython functions and classes:')
for name, obj in inspect.getmembers(Cython):
    if not name.startswith('_'):
        if inspect.isfunction(obj) or inspect.isclass(obj):
            print(f'  {name}: {type(obj).__name__}')
            if hasattr(obj, '__doc__') and obj.__doc__:
                doc_lines = obj.__doc__.strip().split('\n')
                if doc_lines:
                    print(f'    → {doc_lines[0][:80]}')