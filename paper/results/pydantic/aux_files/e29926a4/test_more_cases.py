"""Test more cases to understand the bug pattern"""

from pydantic._migration import getattr_migration
import sys

test_cases = [
    "",  # Empty string
    "nonexistent_module_xyz",  # Module that doesn't exist
    "test module with spaces",  # Invalid module name with spaces
]

for module_name in test_cases:
    print(f"\nTesting module name: {repr(module_name)}")
    print(f"Module in sys.modules: {module_name in sys.modules}")
    
    wrapper = getattr_migration(module_name)
    
    try:
        result = wrapper("test_attr")
        print(f"  Result: {result}")
    except AttributeError as e:
        print(f"  AttributeError (expected): {e}")
    except KeyError as e:
        print(f"  KeyError (BUG!): {e}")
    except Exception as e:
        print(f"  Other error: {type(e).__name__}: {e}")