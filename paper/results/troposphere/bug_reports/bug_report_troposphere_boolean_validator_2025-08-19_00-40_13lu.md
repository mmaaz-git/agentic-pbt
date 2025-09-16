# Bug Report: troposphere.validators.boolean Accepts Unintended Numeric Types

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` validator accepts any numeric type that equals 0 or 1, not just the documented types, due to Python's duck typing and loose equality comparisons.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import boolean

@given(st.floats())
def test_boolean_rejects_float_values(value):
    """Boolean validator should reject float values"""
    if value not in [0.0, 1.0]:
        with pytest.raises(ValueError):
            boolean(value)
    else:
        # This should raise but doesn't - that's the bug
        with pytest.raises(ValueError):
            boolean(value)
```

**Failing input**: `0.0` and `1.0`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere.validators import boolean
from decimal import Decimal
import numpy as np

# All of these should raise ValueError but instead return bool values
print(f"boolean(0.0) = {boolean(0.0)}")  # Returns False, should raise
print(f"boolean(1.0) = {boolean(1.0)}")  # Returns True, should raise
print(f"boolean(Decimal(0)) = {boolean(Decimal(0))}")  # Returns False, should raise
print(f"boolean(Decimal(1)) = {boolean(Decimal(1))}")  # Returns True, should raise
print(f"boolean(np.int32(0)) = {boolean(np.int32(0))}")  # Returns False, should raise
print(f"boolean(np.int32(1)) = {boolean(np.int32(1))}")  # Returns True, should raise
print(f"boolean(complex(0)) = {boolean(complex(0))}")  # Returns False, should raise
print(f"boolean(complex(1)) = {boolean(complex(1))}")  # Returns True, should raise
```

## Why This Is A Bug

The boolean validator's implementation uses `in` operator with lists containing integers 0 and 1, but Python's equality comparison treats numeric types as equal when their values match (e.g., `0.0 == 0` is True). The function is documented to accept only specific types: `True, False, 0, 1, "0", "1", "true", "True", "false", "False"`. Accepting other numeric types violates the expected strict type validation behavior.

## Fix

```diff
def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or (isinstance(x, int) and x == 1) or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or (isinstance(x, int) and x == 0) or x in ["0", "false", "False"]:
         return False
     raise ValueError
```