# Bug Report: troposphere.validators integer_range Error Message Format Bug

**Target**: `troposphere.validators.integer_range`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-01-18

## Summary

The `integer_range` validator accepts float parameters for minimum and maximum bounds but incorrectly formats them as integers in error messages, causing misleading error reporting.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer_range

@given(
    st.floats(min_value=-100, max_value=100).filter(lambda x: x != int(x)),
    st.floats(min_value=-100, max_value=100).filter(lambda x: x != int(x))
)
def test_integer_range_error_message(min_val, max_val):
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    
    validator = integer_range(min_val, max_val)
    test_val = int(min_val) - 1
    
    try:
        validator(test_val)
    except ValueError as e:
        error_msg = str(e)
        assert str(min_val) in error_msg or str(int(min_val)) in error_msg
```

**Failing input**: `integer_range(1.5, 10.5)` with test value `0`

## Reproducing the Bug

```python
from troposphere.validators import integer_range

validator = integer_range(1.5, 10.5)
try:
    validator(0)
except ValueError as e:
    print(f"Error message: {e}")
```

## Why This Is A Bug

The function signature accepts `float` parameters for `minimum_val` and `maximum_val`, but the error message uses `%d` format specifier which truncates floats to integers. This creates misleading error messages that don't accurately reflect the actual validation bounds. Users see "Integer must be between 1 and 10" when the actual bounds are 1.5 and 10.5.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -66,7 +66,7 @@ def integer_range(
         i = int(x)
         if i < minimum_val or i > maximum_val:
             raise ValueError(
-                "Integer must be between %d and %d" % (minimum_val, maximum_val)
+                "Integer must be between %s and %s" % (minimum_val, maximum_val)
             )
         return x
```