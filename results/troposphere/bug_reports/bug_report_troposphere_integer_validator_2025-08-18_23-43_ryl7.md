# Bug Report: troposphere.validators Integer Validator Crash on Infinity

**Target**: `troposphere.validators.integer`
**Severity**: Medium  
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The integer validator crashes with `OverflowError` when given float infinity values instead of raising the expected `ValueError`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import validators

@given(st.one_of(
    st.integers(),
    st.text(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_integer_validator(value):
    """Test the integer validator accepts valid integers and rejects invalid ones"""
    try:
        result = validators.integer(value)
        int(value)
        assert result == value
    except (ValueError, TypeError):
        with pytest.raises(ValueError, match="is not a valid integer"):
            validators.integer(value)
```

**Failing input**: `float('inf')`

## Reproducing the Bug

```python
from troposphere import validators

try:
    validators.integer(float('inf'))
except OverflowError as e:
    print(f"OverflowError: {e}")
    print("Expected: ValueError with 'inf is not a valid integer'")
```

## Why This Is A Bug

The integer validator is expected to raise a `ValueError` with the message "is not a valid integer" for invalid inputs. However, when given float infinity values, it crashes with an `OverflowError` because `int(float('inf'))` raises this exception. This violates the validator's contract and could cause unexpected crashes in code that relies on consistent error handling.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,10 +45,13 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
+        if isinstance(x, float) and (x == float('inf') or x == float('-inf') or x != x):
+            raise ValueError("%r is not a valid integer" % x)
         int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
+    except OverflowError:
+        raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```