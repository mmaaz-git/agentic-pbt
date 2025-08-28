# Bug Report: InquirerPy.separator `__str__` Contract Violation

**Target**: `InquirerPy.separator.Separator`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `Separator` class's `__str__` method violates Python's contract by returning non-string values when initialized with non-string arguments, causing TypeErrors.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from InquirerPy.separator import Separator

@given(st.one_of(
    st.none(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.lists(st.text())
))
def test_separator_str_returns_string(value):
    separator = Separator(value)
    result = str(separator)
    assert isinstance(result, str)
```

**Failing input**: `None`, `42`, `[1, 2, 3]`, `True`, or any non-string value

## Reproducing the Bug

```python
from InquirerPy.separator import Separator

separator = Separator(None)
str(separator)  # TypeError: __str__ returned non-string (type NoneType)

separator = Separator(42)
str(separator)  # TypeError: __str__ returned non-string (type int)

separator = Separator([1, 2, 3])
str(separator)  # TypeError: __str__ returned non-string (type list)
```

## Why This Is A Bug

Python's documentation requires that `__str__` must return a string object. The current implementation returns `self._line` directly without ensuring it's a string, violating this fundamental contract. This causes unexpected TypeErrors when users accidentally pass non-string values to the constructor.

## Fix

```diff
--- a/InquirerPy/separator.py
+++ b/InquirerPy/separator.py
@@ -20,4 +20,4 @@ class Separator:
 
     def __str__(self) -> str:
         """Create string representation of `Separator`."""
-        return self._line
+        return str(self._line)
```