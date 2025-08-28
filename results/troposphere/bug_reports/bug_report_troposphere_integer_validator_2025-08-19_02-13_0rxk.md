# Bug Report: troposphere.validators Integer Validator Accepts Non-Integer Floats

**Target**: `troposphere.validators.integer`
**Severity**: Medium  
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The integer validator incorrectly accepts non-integer float values like 0.5, silently truncating them when converted to int, which causes data loss.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.validators as validators

@given(st.floats().filter(lambda x: not x.is_integer()))
def test_integer_validator_rejects_non_integer_floats(value):
    """Test that integer validator rejects non-integer floats."""
    try:
        validators.integer(value)
        assert False, f"Should have raised ValueError for non-integer float {value}"
    except ValueError:
        pass  # Expected
```

**Failing input**: `0.5`, `1.5`, `3.14`, etc.

## Reproducing the Bug

```python
import troposphere.validators as validators

result = validators.integer(0.5)
print(f"integer(0.5) = {result}")  # Returns 0.5
print(f"int(result) = {int(result)}")  # Converts to 0, losing precision

result2 = validators.integer(3.14)
print(f"integer(3.14) = {result2}")  # Returns 3.14
print(f"int(result2) = {int(result2)}")  # Converts to 3, losing precision
```

## Why This Is A Bug

The integer validator is meant to validate integer values but currently accepts any value that can be converted to int, including floats. This causes silent data loss when non-integer floats are truncated. The validator should reject non-integer values rather than silently accepting them and losing precision during conversion.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,7 +45,10 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        if isinstance(x, float) and not x.is_integer():
+            raise ValueError("%r is not an integer" % x)
+        int_val = int(x)
+        # Additional check for string representations
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
```