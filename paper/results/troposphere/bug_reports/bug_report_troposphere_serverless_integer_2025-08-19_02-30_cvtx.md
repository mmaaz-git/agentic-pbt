# Bug Report: troposphere.serverless.integer() Accepts Non-Integer Floats

**Target**: `troposphere.serverless.integer`
**Severity**: High  
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer()` validation function incorrectly accepts non-integer float values like 0.5, 3.14, etc., returning them unchanged instead of raising ValueError. Additionally, it crashes with OverflowError on infinity values instead of ValueError.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
import troposphere.serverless as serverless

@given(st.floats())
def test_integer_rejects_non_integer_floats(value):
    """Test that integer() only accepts integer-valued inputs."""
    if value.is_integer() and not math.isnan(value) and not math.isinf(value):
        result = serverless.integer(value)
        assert int(result) == int(value)
    else:
        with pytest.raises(ValueError):
            serverless.integer(value)
```

**Failing input**: `0.5`

## Reproducing the Bug

```python
import troposphere.serverless as serverless

result1 = serverless.integer(0.5)
print(f"integer(0.5) = {result1}, type = {type(result1)}")

result2 = serverless.integer(3.14159)
print(f"integer(3.14159) = {result2}, type = {type(result2)}")

try:
    result3 = serverless.integer(float('inf'))
    print(f"integer(inf) = {result3}")
except OverflowError as e:
    print(f"integer(inf) raised OverflowError: {e}")
```

## Why This Is A Bug

The `integer()` function is meant to validate that a value is an integer. However, it only checks if `int(x)` succeeds without error, then returns the original value unchanged. This means:
1. Non-integer floats like 0.5 are accepted and returned as floats
2. The function doesn't actually validate that the input IS an integer
3. Infinity values cause OverflowError instead of the expected ValueError

## Fix

```diff
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        int_val = int(x)
+        # Check if conversion preserved the value (for floats)
+        if isinstance(x, float) and x != int_val:
+            raise ValueError("%r is not a valid integer" % x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
+    except OverflowError:
+        raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```