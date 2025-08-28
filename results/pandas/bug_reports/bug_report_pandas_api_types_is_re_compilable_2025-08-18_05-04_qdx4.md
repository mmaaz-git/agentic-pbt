# Bug Report: pandas.api.types.is_re_compilable Crashes on Invalid Regex Patterns

**Target**: `pandas.api.types.is_re_compilable`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `is_re_compilable` function raises an unhandled `re.PatternError` exception when given invalid regex patterns, instead of returning `False` as expected.

## Property-Based Test

```python
@given(st.text())
def test_is_re_compilable(text):
    """Property: is_re_compilable should not crash on any string"""
    result = types.is_re_compilable(text)
    assert isinstance(result, bool)
    
    if result:
        import re
        try:
            re.compile(text)
        except:
            assert False, f"is_re_compilable returned True but pattern '{text}' cannot be compiled"
```

**Failing input**: `'['`

## Reproducing the Bug

```python
import pandas.api.types as types

invalid_patterns = ['[', '(', '*', '(?P<', '\\']

for pattern in invalid_patterns:
    try:
        result = types.is_re_compilable(pattern)
        print(f"is_re_compilable('{pattern}') = {result}")
    except Exception as e:
        print(f"is_re_compilable('{pattern}') raised {type(e).__name__}: {e}")
```

## Why This Is A Bug

The function is documented to return a boolean indicating whether the object can be compiled as a regex pattern. When given an invalid regex pattern, it should return `False` rather than raising an exception. The current implementation only catches `TypeError` but not `re.error` (which includes `re.PatternError`).

## Fix

```diff
--- a/pandas/core/dtypes/inference.py
+++ b/pandas/core/dtypes/inference.py
@@ -186,7 +186,7 @@ def is_re_compilable(obj) -> bool:
     """
     try:
         re.compile(obj)
-    except TypeError:
+    except (TypeError, re.error):
         return False
     else:
         return True
```