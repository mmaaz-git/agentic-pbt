# Bug Report: trino.transaction IsolationLevel.check() Accepts Non-Integer Types

**Target**: `trino.transaction.IsolationLevel.check()`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `IsolationLevel.check()` method incorrectly accepts non-integer numeric types (float, bool, Decimal, complex) that are numerically equal to valid isolation levels, violating type safety.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from trino.transaction import IsolationLevel

@given(st.one_of(st.floats(), st.booleans()))
def test_isolation_level_check_rejects_non_integers(value):
    """Test that check() only accepts integers, not other numeric types."""
    if not isinstance(value, int) or isinstance(value, bool):
        with pytest.raises((ValueError, TypeError)):
            IsolationLevel.check(value)
```

**Failing input**: `0.0` (also `1.0`, `2.0`, `3.0`, `4.0`, `True`, `False`)

## Reproducing the Bug

```python
from trino.transaction import IsolationLevel

# These should raise ValueError but don't
result1 = IsolationLevel.check(0.0)  
print(f"check(0.0) = {result1}, type = {type(result1)}")  # 0.0, <class 'float'>

result2 = IsolationLevel.check(True)
print(f"check(True) = {result2}, type = {type(result2)}")  # True, <class 'bool'>

result3 = IsolationLevel.check(False)
print(f"check(False) = {result3}, type = {type(result3)}")  # False, <class 'bool'>

# Also affects Decimal and complex numbers
from decimal import Decimal
result4 = IsolationLevel.check(Decimal('2'))
print(f"check(Decimal('2')) = {result4}, type = {type(result4)}")  # 2, <class 'decimal.Decimal'>
```

## Why This Is A Bug

The `check()` method is designed to validate integer isolation levels but uses the `in` operator with a set, which performs equality comparison. In Python, `0.0 == 0` and `True == 1`, causing these non-integer values to be incorrectly accepted. This violates type safety - the method should only accept and return integers but instead accepts and returns values of incorrect types.

## Fix

```diff
@classmethod
def check(cls, level: int) -> int:
+   if not isinstance(level, int) or isinstance(level, bool):
+       raise ValueError("invalid isolation level {}".format(level))
    if level not in cls.values():
        raise ValueError("invalid isolation level {}".format(level))
    return level
```