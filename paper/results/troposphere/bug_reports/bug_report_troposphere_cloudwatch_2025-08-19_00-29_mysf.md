# Bug Report: troposphere.cloudwatch Type Validators Accept Boolean Values

**Target**: `troposphere.cloudwatch` validators (integer, double)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer()` and `double()` type validators incorrectly accept boolean values due to Python's type hierarchy where `bool` is a subclass of `int`. This violates CloudFormation's type system where booleans and integers are distinct types.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import cloudwatch

@given(st.booleans())
def test_integer_validator_rejects_booleans(value):
    """integer validator should reject boolean values."""
    # Booleans should not be considered valid integers for CloudFormation
    assert cloudwatch.integer(value) == False

@given(st.booleans()) 
def test_double_validator_rejects_booleans(value):
    """double validator should reject boolean values."""
    # Booleans should not be considered valid doubles for CloudFormation
    assert cloudwatch.double(value) == False
```

**Failing input**: `False` (and `True`)

## Reproducing the Bug

```python
def integer(x):
    return isinstance(x, int)

def double(x):
    return isinstance(x, (int, float))

print(f"integer(True) = {integer(True)}")   # Returns True, should be False
print(f"integer(False) = {integer(False)}") # Returns True, should be False
print(f"double(True) = {double(True)}")     # Returns True, should be False
print(f"double(False) = {double(False)}")   # Returns True, should be False

# This allows invalid CloudFormation configurations
class Alarm:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

alarm = Alarm(EvaluationPeriods=True)  # Should be rejected
print(f"Alarm accepts EvaluationPeriods=True: {alarm.EvaluationPeriods}")
```

## Why This Is A Bug

CloudFormation distinguishes between boolean and numeric types. A CloudFormation template with `EvaluationPeriods: true` or `Threshold: false` would be rejected by AWS, but the current validators would incorrectly accept these values. This occurs because Python's `bool` type is a subclass of `int`, causing `isinstance(True, int)` to return `True`.

## Fix

```diff
def integer(x):
-    return isinstance(x, int)
+    return isinstance(x, int) and not isinstance(x, bool)

def double(x):
-    return isinstance(x, (int, float))
+    return isinstance(x, (int, float)) and not isinstance(x, bool)
```