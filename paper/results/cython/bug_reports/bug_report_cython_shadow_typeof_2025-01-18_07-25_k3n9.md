# Bug Report: Cython.Shadow.typeof Returns Strings Instead of Type Objects

**Target**: `Cython.Shadow.typeof`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-01-18

## Summary

The `typeof()` function in Cython.Shadow returns string representations of types (e.g., `'int'`, `'float'`) instead of actual Python type objects, contradicting expected behavior and containing commented-out correct implementation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import Cython.Shadow as Shadow

@given(st.integers())
def test_typeof_integer(value):
    """Property: typeof should return the correct Python type for integers."""
    assert Shadow.typeof(value) == int
```

**Failing input**: `0` (or any integer)

## Reproducing the Bug

```python
import Cython.Shadow as Shadow

# Bug: typeof returns strings instead of type objects
value = 42
result = Shadow.typeof(value)

print(f"Shadow.typeof({value}) = {result!r}")
print(f"Type of result: {type(result)}")
print(f"Expected: {type(value)}")

# This comparison fails
assert result == int, f"Expected {int}, got {result!r}"
```

## Why This Is A Bug

1. The function name `typeof` suggests it should return type information like Python's built-in `type()` function
2. The source code contains a commented line `# return type(arg)` showing the correct implementation was considered
3. Returning strings breaks code that expects type objects for `isinstance()` checks or type comparisons
4. No documentation indicates that returning strings is the intended behavior

## Fix

```diff
def typeof(arg):
-    return arg.__class__.__name__
-    # return type(arg)
+    return type(arg)
```