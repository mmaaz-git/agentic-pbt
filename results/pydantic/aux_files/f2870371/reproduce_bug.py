"""Minimal reproduction of the __dict__ access bug in pydantic.decorator.getattr_migration"""

import sys
from pydantic.decorator import getattr_migration

# Create a test module
module_name = 'test_module'
module = type(sys)(module_name)
sys.modules[module_name] = module

# The module has __dict__ as a descriptor attribute
print(f"Module has __dict__: {hasattr(module, '__dict__')}")
print(f"Direct access to __dict__ works: {module.__dict__ is not None}")

# Create wrapper using getattr_migration
wrapper = getattr_migration(module_name)

# Try to access __dict__ through the wrapper
try:
    result = wrapper('__dict__')
    print(f"Success: wrapper('__dict__') returned {type(result)}")
except AttributeError as e:
    print(f"BUG: wrapper('__dict__') raised AttributeError: {e}")
    print(f"Expected: Should return the module's __dict__")

# Show that other descriptor attributes also fail
for attr in ['__class__', '__module__', '__name__']:
    try:
        direct = getattr(module, attr)
        print(f"\nDirect access to {attr}: {direct!r}")
        wrapped = wrapper(attr)
        print(f"Wrapper access to {attr}: {wrapped!r}")
    except AttributeError as e:
        print(f"BUG: wrapper('{attr}') raised AttributeError: {e}")

# Clean up
del sys.modules[module_name]