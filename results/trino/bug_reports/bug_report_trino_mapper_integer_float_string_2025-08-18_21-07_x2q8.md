# Bug Report: trino.mapper.IntegerValueMapper Inconsistent Float Handling

**Target**: `trino.mapper.IntegerValueMapper`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

IntegerValueMapper inconsistently handles float values: it successfully converts float objects to integers but fails when the same values are provided as strings, creating an unexpected asymmetry in the API.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from trino.mapper import IntegerValueMapper

@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_from_float_string(value):
    """IntegerValueMapper should handle float strings consistently with float objects."""
    mapper = IntegerValueMapper()
    
    # Direct float object works
    result_from_float = mapper.map(value)
    assert result_from_float == int(value)
    
    # String representation should work the same way
    if value == int(value):  # Whole number
        result_from_string = mapper.map(str(value))
        assert result_from_string == int(value)
```

**Failing input**: `'0.0'`, `'1.0'`, `'42.0'`, etc.

## Reproducing the Bug

```python
from trino.mapper import IntegerValueMapper

mapper = IntegerValueMapper()

# Float object works
print(f"Direct float 1.0 -> {mapper.map(1.0)}")

# String of the same float fails
try:
    result = mapper.map('1.0')
    print(f"String '1.0' -> {result}")
except ValueError as e:
    print(f"String '1.0' raises: {e}")

# This inconsistency is confusing:
# mapper.map(42.0) returns 42
# mapper.map('42.0') raises ValueError
```

## Why This Is A Bug

The mapper accepts float objects and truncates them to integers (e.g., `3.14` → `3`), but rejects string representations of the same values. This inconsistency violates the principle of least surprise and could cause issues if data format changes between float and string representations.

## Fix

```diff
--- a/trino/mapper.py
+++ b/trino/mapper.py
@@ -57,8 +57,13 @@ class IntegerValueMapper(ValueMapper[int]):
             return None
         if isinstance(value, int):
             return value
-        # int(3.1) == 3 but server won't send such values for integer types
-        return int(value)
+        # int(3.1) == 3 but server won't send such values for integer types
+        try:
+            return int(value)
+        except ValueError:
+            # Try converting through float for string representations like '1.0'
+            # This maintains consistency with how we handle float objects
+            return int(float(value))
```