# Bug Report: troposphere.xray integer() Crashes on Infinity

**Target**: `troposphere.xray.integer`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `integer()` validation function raises `OverflowError` instead of the expected `ValueError` when given float infinity values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.xray as xray
import math

@given(st.one_of(
    st.floats(allow_nan=True, allow_infinity=True),
    st.just(float('nan')),
    st.just(float('inf')),
    st.just(float('-inf'))
))
def test_integer_with_special_floats(x):
    """integer() should handle special float values correctly."""
    if math.isnan(x) or math.isinf(x):
        try:
            xray.integer(x)
            assert False, f"integer() should raise ValueError for {x}"
        except ValueError:
            pass  # Expected
```

**Failing input**: `float('inf')`

## Reproducing the Bug

```python
import troposphere.xray as xray

try:
    result = xray.integer(float('inf'))
    print(f"Unexpected success: {result}")
except ValueError:
    print("ValueError raised (expected)")
except OverflowError as e:
    print(f"OverflowError raised (BUG): {e}")
```

## Why This Is A Bug

The `integer()` function is documented to raise `ValueError` for invalid inputs. However, when given infinity, it raises `OverflowError` instead. This violates the expected exception contract and could cause issues for code that specifically catches `ValueError` to handle validation failures.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
+       if hasattr(x, '__float__'):
+           f = float(x)
+           import math
+           if math.isnan(f) or math.isinf(f):
+               raise ValueError("%r is not a valid integer" % x)
        int(x)
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
+   except OverflowError:
+       raise ValueError("%r is not a valid integer" % x)
    else:
        return x
```