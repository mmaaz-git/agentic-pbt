# Bug Report: trino.constants Mutable List Constants

**Target**: `trino.constants`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `LENGTH_TYPES`, `PRECISION_TYPES`, and `SCALE_TYPES` constants in `trino.constants` are mutable lists that can be modified at runtime, violating the expectation that constants should be immutable.

## Property-Based Test

```python
def test_constants_immutability():
    """Test that constants cannot be mutated"""
    import trino.constants as constants
    
    # Constants should be immutable
    original_length = len(constants.LENGTH_TYPES)
    try:
        constants.LENGTH_TYPES.append("test")
        # If we get here, the list is mutable - this is the bug
        assert False, "LENGTH_TYPES should be immutable but can be modified"
    except (AttributeError, TypeError):
        # This is the expected behavior for immutable constants
        pass
```

**Failing input**: Direct mutation of list constants succeeds when it should fail

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')
import trino.constants as constants

# These "constants" can be mutated
print("Original LENGTH_TYPES:", constants.LENGTH_TYPES)
constants.LENGTH_TYPES.append("corrupted")
print("Mutated LENGTH_TYPES:", constants.LENGTH_TYPES)

print("\nOriginal PRECISION_TYPES:", constants.PRECISION_TYPES)
constants.PRECISION_TYPES.clear()
print("Cleared PRECISION_TYPES:", constants.PRECISION_TYPES)

print("\nOriginal SCALE_TYPES:", constants.SCALE_TYPES)
constants.SCALE_TYPES.extend(["bad1", "bad2"])
print("Extended SCALE_TYPES:", constants.SCALE_TYPES)
```

## Why This Is A Bug

Module-level variables named with uppercase letters (like `LENGTH_TYPES`) are conventionally constants in Python and should be immutable. Allowing mutation of these "constants" violates the principle of least surprise and could lead to bugs if code inadvertently modifies these values, affecting other parts of the program that expect them to remain unchanged.

## Fix

```diff
--- a/trino/constants.py
+++ b/trino/constants.py
@@ -65,7 +65,7 @@ CLIENT_CAPABILITIES = ','.join([CLIENT_CAPABILITY_PARAMETRIC_DATETIME, CLIENT_C
 HEADER_SET_AUTHORIZATION_USER = "X-Trino-Set-Authorization-User"
 HEADER_RESET_AUTHORIZATION_USER = "X-Trino-Reset-Authorization-User"
 
-LENGTH_TYPES = ["char", "varchar"]
-PRECISION_TYPES = ["time", "time with time zone", "timestamp", "timestamp with time zone", "decimal"]
-SCALE_TYPES = ["decimal"]
+LENGTH_TYPES = ("char", "varchar")
+PRECISION_TYPES = ("time", "time with time zone", "timestamp", "timestamp with time zone", "decimal")
+SCALE_TYPES = ("decimal",)
```