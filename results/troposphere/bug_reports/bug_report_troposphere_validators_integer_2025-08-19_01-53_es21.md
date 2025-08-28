# Bug Report: troposphere.validators Integer Validator Crashes on Infinity

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `integer` validator function crashes with an `OverflowError` when given float infinity instead of raising a `ValueError` as expected.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer

@given(st.floats())
def test_integer_validator_handles_all_floats(value):
    """Test that integer validator handles all float values gracefully."""
    try:
        result = integer(value)
    except ValueError:
        pass  # Expected for non-integer floats
    except OverflowError:
        raise AssertionError(f"integer validator crashed on {value}")
```

**Failing input**: `inf`

## Reproducing the Bug

```python
from troposphere.validators import integer

result = integer(float('inf'))
```

## Why This Is A Bug

The `integer` validator is supposed to validate whether a value can be converted to an integer. When it cannot, it should raise a `ValueError` with a descriptive message. Instead, it crashes with an unhandled `OverflowError` when given infinity, breaking the expected API contract.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,7 +45,10 @@
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
-    except (ValueError, TypeError):
+    except OverflowError:
+        raise ValueError("%r is not a valid integer" % x)
+    except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```