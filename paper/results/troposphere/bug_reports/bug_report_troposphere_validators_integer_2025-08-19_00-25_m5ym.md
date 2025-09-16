# Bug Report: troposphere.validators.integer OverflowError with Infinity

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `integer` validator function crashes with an unhandled OverflowError when given float infinity values, causing property validation to fail unexpectedly instead of raising a proper ValueError.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.cloud9 as cloud9

@given(
    stop_time=st.one_of(
        st.just(float('inf')),
        st.just(float('-inf'))
    )
)
def test_automatic_stop_invalid_types(stop_time):
    """Test AutomaticStopTimeMinutes with infinity values"""
    try:
        env = cloud9.EnvironmentEC2(
            "TestEnv",
            ImageId="ami-12345678",
            InstanceType="t2.micro",
            AutomaticStopTimeMinutes=stop_time
        )
        env.to_dict()
        assert False, f"Invalid value {stop_time} was accepted for integer field"
    except ValueError:
        pass  # Expected
    except OverflowError:
        raise AssertionError("OverflowError instead of ValueError")
```

**Failing input**: `float('inf')`

## Reproducing the Bug

```python
import troposphere.cloud9 as cloud9

env = cloud9.EnvironmentEC2(
    "TestEnv",
    ImageId="ami-12345678",
    InstanceType="t2.micro",
    AutomaticStopTimeMinutes=float('inf')
)
```

## Why This Is A Bug

The integer validator is supposed to validate that a value can be converted to an integer and raise a ValueError with a descriptive message if not. However, when given float infinity, it crashes with an unhandled OverflowError. This violates the expected contract that invalid inputs should result in a ValueError with the message "%r is not a valid integer".

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,8 +45,11 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
+        if isinstance(x, float) and (x == float('inf') or x == float('-inf')):
+            raise ValueError("%r is not a valid integer" % x)
         int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
+    except OverflowError:
+        raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```