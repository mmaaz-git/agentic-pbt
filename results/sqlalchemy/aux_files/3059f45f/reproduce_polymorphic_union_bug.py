"""Minimal reproduction of polymorphic_union bug with empty table map."""

import sqlalchemy.orm as orm

# Attempt to create a polymorphic union with an empty table map
try:
    result = orm.polymorphic_union({}, 'type')
    print(f"Unexpectedly succeeded, result: {result}")
except IndexError as e:
    print(f"Bug confirmed! IndexError raised: {e}")
    print("\nThis should not raise an IndexError.")
    print("Expected behavior: Either return a valid empty union or raise a more appropriate exception")
    
    # Get full traceback
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
except (ValueError, TypeError) as e:
    print(f"Raised appropriate exception: {type(e).__name__}: {e}")
except Exception as e:
    print(f"Raised unexpected exception: {type(e).__name__}: {e}")