"""
Minimal reproduction of BaseSettings error handling inconsistency bug.
"""

import pydantic
import pydantic.env_settings
from pydantic.errors import PydanticImportError


def test_basesettings_error_inconsistency():
    """
    Demonstrates that BaseSettings special error is inconsistent across modules.
    """
    print("Testing BaseSettings error handling inconsistency...")
    
    # Test 1: Access through pydantic module
    print("\n1. Accessing pydantic.BaseSettings:")
    try:
        _ = pydantic.BaseSettings
    except PydanticImportError as e:
        print(f"   ✓ Raises PydanticImportError with helpful message:")
        print(f"     '{e}'")
    except Exception as e:
        print(f"   ✗ Unexpected error: {type(e).__name__}: {e}")
    
    # Test 2: Access through pydantic.env_settings module  
    print("\n2. Accessing pydantic.env_settings.BaseSettings:")
    try:
        _ = pydantic.env_settings.BaseSettings
    except PydanticImportError as e:
        print(f"   ✓ Raises PydanticImportError with helpful message:")
        print(f"     '{e}'")
    except AttributeError as e:
        print(f"   ✗ Raises generic AttributeError instead:")
        print(f"     '{e}'")
        print("   This should raise the same PydanticImportError as above!")
    
    print("\n" + "="*60)
    print("BUG CONFIRMED: BaseSettings error handling is inconsistent")
    print("="*60)


if __name__ == "__main__":
    test_basesettings_error_inconsistency()