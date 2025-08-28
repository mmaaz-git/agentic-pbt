# Bug Report: troposphere.validators.integer Raises OverflowError Instead of ValueError

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer` validator function raises `OverflowError` when given float infinity values instead of the expected `ValueError`, breaking error handling consistency.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import healthlake

@given(
    invalid_value=st.one_of(
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers()),
        st.floats(),
    )
)
def test_created_at_type_enforcement(invalid_value):
    """Test that CreatedAt enforces correct types for properties."""
    try:
        created_at = healthlake.CreatedAt(Nanos=invalid_value, Seconds="100")
        created_at.to_dict()
        int(invalid_value)
    except (ValueError, TypeError):
        pass
```

**Failing input**: `float('inf')`

## Reproducing the Bug

```python
from troposphere.validators import integer

try:
    result = integer(float('inf'))
    print(f"Unexpectedly succeeded: {result}")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")
except OverflowError as e:
    print(f"Incorrectly raised OverflowError: {e}")

try:
    result = integer(float('-inf'))
    print(f"Unexpectedly succeeded: {result}")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")
except OverflowError as e:
    print(f"Incorrectly raised OverflowError: {e}")
```

## Why This Is A Bug

The `integer` validator is documented to raise `ValueError` for invalid inputs, as seen in line 50: `raise ValueError("%r is not a valid integer" % x)`. However, when given float infinity values, it raises `OverflowError` instead. This inconsistency breaks error handling expectations and makes it harder for users to properly catch validation errors.

Users expecting to catch `ValueError` for all validation failures will miss `OverflowError` exceptions, potentially causing unexpected crashes in production code.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,7 +45,10 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        if isinstance(x, float) and (x == float('inf') or x == float('-inf')):
+            raise ValueError("%r is not a valid integer" % x)
+        else:
+            int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
+    except OverflowError:
+        raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```