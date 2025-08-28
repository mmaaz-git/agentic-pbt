"""Minimal reproduction of the KeyError bug in pydantic.utils.getattr_migration"""

import sys
import pydantic.utils

# Test 1: Module that doesn't exist in sys.modules
print("Test 1: Non-existent module '0'")
wrapper = pydantic.utils.getattr_migration('0')

try:
    result = wrapper('test_attr')
    print(f"Unexpectedly got result: {result}")
except KeyError as e:
    print(f"Got KeyError: {e}")
    print("Bug confirmed: Should raise AttributeError, not KeyError")
except AttributeError as e:
    print(f"Got expected AttributeError: {e}")

print("\n" + "="*50 + "\n")

# Test 2: Another non-existent module
print("Test 2: Non-existent module 'nonexistent_module'")
wrapper2 = pydantic.utils.getattr_migration('nonexistent_module')

try:
    result = wrapper2('some_attr')
    print(f"Unexpectedly got result: {result}")
except KeyError as e:
    print(f"Got KeyError: {e}")
    print("Bug confirmed: Should raise AttributeError, not KeyError")
except AttributeError as e:
    print(f"Got expected AttributeError: {e}")

print("\n" + "="*50 + "\n")

# Test 3: Check what the error should be
print("Test 3: Expected behavior - module that exists")
# Create a dummy module
import types
dummy_module = types.ModuleType('dummy_module')
sys.modules['dummy_module'] = dummy_module

wrapper3 = pydantic.utils.getattr_migration('dummy_module')
try:
    result = wrapper3('nonexistent_attr')
    print(f"Unexpectedly got result: {result}")
except AttributeError as e:
    print(f"Got expected AttributeError: {e}")
    print("This is the expected error format")
    
# Clean up
del sys.modules['dummy_module']