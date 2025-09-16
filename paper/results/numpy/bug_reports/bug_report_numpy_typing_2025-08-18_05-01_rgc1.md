# Bug Report: numpy.typing Attribute Error Message Format Inconsistency

**Target**: `numpy.typing.__getattr__`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `__getattr__` method in `numpy.typing` uses `repr()` on attribute names in error messages, causing inconsistent formatting compared to standard Python AttributeError messages, especially for special characters.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import numpy.typing as npt

@given(st.text().filter(lambda x: x not in dir(npt) and x != "NBitBase" and repr(x) != f"'{x}'"))
def test_error_message_repr_inconsistency(attr_name):
    try:
        getattr(npt, attr_name)
        assert False
    except AttributeError as e:
        error_msg = str(e)
        expected_with_str = f"module 'numpy.typing' has no attribute '{attr_name}'"
        expected_with_repr = f"module 'numpy.typing' has no attribute {repr(attr_name)}"
        assert error_msg == expected_with_repr  # Bug: uses repr
        assert error_msg != expected_with_str  # Should use raw string
```

**Failing input**: `'\n'` (newline character)

## Reproducing the Bug

```python
import numpy.typing as npt

attr_name = '\n'
try:
    getattr(npt, attr_name)
except AttributeError as e:
    error_msg = str(e)
    print(f"Actual: {repr(error_msg)}")
    print(f"Expected: {repr(f\"module 'numpy.typing' has no attribute '{attr_name}'\"}")
```

## Why This Is A Bug

Python's standard `AttributeError` messages use the raw attribute name in quotes, not its `repr()`. For example, `getattr(object(), '\n')` produces `"type object 'object' has no attribute '\n'"`, not `"... has no attribute '\\n'"`. The numpy.typing module breaks this convention by using `{name!r}` instead of `'{name}'` in the f-string.

## Fix

```diff
--- a/numpy/typing/__init__.py
+++ b/numpy/typing/__init__.py
@@ -186,7 +186,7 @@ def __getattr__(name: str):
     if name in __DIR_SET:
         return globals()[name]
 
-    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
+    raise AttributeError(f"module {__name__!r} has no attribute '{name}'")
 
 
 if __doc__ is not None:
```