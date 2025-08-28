import bs4.formatter
import inspect

members = inspect.getmembers(bs4.formatter)
public_members = [(name, obj) for name, obj in members if not name.startswith('_')]

print('Public members in bs4.formatter:')
for name, obj in public_members:
    print(f'  {name}: {type(obj).__name__}')
    
# Let's also explore classes
classes = [obj for name, obj in public_members if inspect.isclass(obj)]
print('\nClasses found:')
for cls in classes:
    print(f'\n{cls.__name__}:')
    print(f'  Docstring: {cls.__doc__[:200] if cls.__doc__ else "None"}...')
    methods = [m for m in dir(cls) if not m.startswith('_')]
    print(f'  Public methods: {methods}')