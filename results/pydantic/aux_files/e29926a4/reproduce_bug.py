"""Minimal reproduction of the empty module name bug in pydantic._migration.getattr_migration"""

from pydantic._migration import getattr_migration

# Create a wrapper for an empty module name
wrapper = getattr_migration("")

# Try to access any attribute (that's not in the special cases)
try:
    result = wrapper("test_attribute")
    print(f"Unexpectedly got result: {result}")
except AttributeError as e:
    print(f"Got expected AttributeError: {e}")
except KeyError as e:
    print(f"BUG: Got KeyError instead of AttributeError: {e}")
    print("\nThis is a bug because:")
    print("1. The function should handle non-existent modules gracefully")
    print("2. It should raise AttributeError, not KeyError")
    print("3. Empty string is a valid string input that shouldn't crash")