# Bug Report: click.types.BoolParamType AttributeError on Integer Input

**Target**: `click.types.BoolParamType`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

BoolParamType.convert() crashes with AttributeError when given integer values other than 0, 1, True, or False, attempting to call .strip() on non-string input.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import click.types

@given(st.integers())
def test_bool_integer_crash(value):
    """Test that BoolParamType crashes on integer inputs other than bool"""
    bool_type = click.types.BoolParamType()
    
    if value not in {0, 1, True, False}:
        try:
            result = bool_type.convert(value, None, None)
        except AttributeError as e:
            assert False, f"BoolParamType should handle integer {value} gracefully"
        except click.types.BadParameter:
            pass
```

**Failing input**: `value=-1`

## Reproducing the Bug

```python
import click.types

bool_type = click.types.BoolParamType()
result = bool_type.convert(-1, None, None)
```

## Why This Is A Bug

The BoolParamType.convert() method is supposed to handle various input types and either convert them to boolean or raise a BadParameter exception. However, it crashes with an AttributeError when given integer values that aren't boolean-like (0, 1, True, False). The code checks for True/False at line 667-668, but then unconditionally calls value.strip().lower() at line 670, assuming the value is a string.

## Fix

```diff
--- a/click/types.py
+++ b/click/types.py
@@ -664,11 +664,14 @@ class BoolParamType(ParamType):
     def convert(
         self, value: t.Any, param: Parameter | None, ctx: Context | None
     ) -> t.Any:
         if value in {False, True}:
             return bool(value)
 
+        if not isinstance(value, str):
+            value = str(value)
+
         norm = value.strip().lower()
 
         if norm in {"1", "true", "t", "yes", "y", "on"}:
             return True
 
         if norm in {"0", "false", "f", "no", "n", "off"}:
```