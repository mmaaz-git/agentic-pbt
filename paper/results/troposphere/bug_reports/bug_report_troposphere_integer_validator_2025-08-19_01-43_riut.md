# Bug Report: troposphere Integer Validator OverflowError

**Target**: `troposphere.validators.integer`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The integer validator raises an unhandled OverflowError when given float infinity values instead of the expected ValueError.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import validators

@given(st.one_of(
    st.integers(),
    st.floats(),
    st.text(),
    st.none(),
    st.booleans(),
    st.lists(st.integers())
))
def test_integer_validator_property(value):
    """Integer validator should accept values convertible to int"""
    try:
        result = validators.integer(value)
        int_value = int(value)
        assert result == value
    except ValueError as e:
        assert 'not a valid integer' in str(e)
        try:
            int(value)
            if not isinstance(value, bool):
                assert False, f"Value {value!r} can be int() but validator rejected"
        except (ValueError, TypeError):
            pass
```

**Failing input**: `float('inf')`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import validators

validators.integer(float('inf'))
```

## Why This Is A Bug

The integer validator's contract is to raise ValueError for invalid integers, as seen in its error message "not a valid integer". However, it leaks an OverflowError for infinity values, violating its API contract. Validators should handle all invalid inputs consistently.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,7 +45,7 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
-    except (ValueError, TypeError):
+    except (ValueError, TypeError, OverflowError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```