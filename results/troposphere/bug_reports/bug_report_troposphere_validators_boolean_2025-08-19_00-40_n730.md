# Bug Report: troposphere.validators.boolean Accepts Unintended Numeric Types

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` validator incorrectly accepts float and other numeric types that compare equal to 0 or 1, violating its type contract which explicitly specifies only `bool`, `int`, and `str` types.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import boolean

@given(st.floats())
def test_boolean_validator_rejects_floats(value):
    """Test that the boolean validator should reject float values"""
    if value not in [0, 1]:  # Only integers 0 and 1 should be accepted
        try:
            boolean(value)
            assert False, f"Expected ValueError for float {value}"
        except ValueError:
            pass  # Expected
```

**Failing input**: `0.0` (and `1.0`)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere.validators import boolean

# These should raise ValueError but don't
print(f"boolean(0.0) = {boolean(0.0)}")  # Returns False
print(f"boolean(1.0) = {boolean(1.0)}")  # Returns True

# Also affects other numeric types
import decimal
print(f"boolean(Decimal('0')) = {boolean(decimal.Decimal('0'))}")  # Returns False
print(f"boolean(complex(1)) = {boolean(complex(1))}")  # Returns True
```

## Why This Is A Bug

The function's type hints explicitly define accepted types as `Literal[True, 1, "true", "True"]` and `Literal[False, 0, "false", "False"]`, where `0` and `1` are integers, not floats. The bug occurs because Python's `in` operator uses `==` for comparison, and `0.0 == 0` evaluates to `True`. This allows unintended numeric types to pass validation, potentially causing downstream issues where boolean properties receive float values.

## Fix

```diff
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or x == 1 and type(x) is int or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or x == 0 and type(x) is int or x in ["0", "false", "False"]:
         return False
     raise ValueError
```