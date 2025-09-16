# Bug Report: troposphere.ses.boolean Accepts Complex Numbers

**Target**: `troposphere.ses.boolean`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` validator in troposphere.ses incorrectly accepts complex numbers `0j` and `1+0j`, converting them to `False` and `True` respectively.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.ses as ses

@given(st.complex_numbers())
def test_boolean_rejects_complex(x):
    """Property: boolean validator should reject all complex numbers"""
    try:
        result = ses.boolean(x)
        # Complex numbers should never be accepted
        assert False, f"Complex number {x!r} was accepted as boolean"
    except (ValueError, TypeError):
        pass  # Expected behavior
```

**Failing input**: `complex(0.0, 0.0)` (aka `0j`) and `complex(1.0, 0.0)` (aka `1+0j`)

## Reproducing the Bug

```python
import troposphere.ses as ses

# Bug: Complex numbers are accepted
assert ses.boolean(0j) == False
assert ses.boolean(1+0j) == True

# This happens because Python's equality comparison
# treats 0j == 0 and (1+0j) == 1 as True
print(0j in [False, 0])  # True - causes the bug
print((1+0j) in [True, 1])  # True - causes the bug
```

## Why This Is A Bug

A boolean validator should only accept boolean-like values (booleans, 0/1 integers, and specific strings). Accepting complex numbers violates the principle of least surprise and the implied contract of a "boolean" validator. This could lead to unexpected behavior when complex numbers are accidentally passed to AWS CloudFormation boolean properties.

## Fix

```diff
--- a/troposphere/validators.py
+++ b/troposphere/validators.py
@@ -1,6 +1,8 @@
 def boolean(x: Any) -> bool:
+    if isinstance(x, complex):
+        raise ValueError(f"Complex numbers are not valid boolean values: {x!r}")
     if x in [True, 1, "1", "true", "True"]:
         return True
     if x in [False, 0, "0", "false", "False"]:
         return False
     raise ValueError
```