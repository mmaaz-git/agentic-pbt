# Bug Report: bs4.formatter Float Indent Parameter Handling

**Target**: `bs4.formatter.Formatter`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The Formatter class incorrectly handles float values for the indent parameter, always converting them to a single space instead of treating them like their integer equivalents.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from bs4.formatter import Formatter

@given(st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False))
def test_indent_float_handling(float_value):
    """Test that float indent values are handled consistently with integers."""
    formatter = Formatter(indent=float_value)
    
    # Floats should behave like their integer equivalents
    int_equivalent = int(float_value)
    int_formatter = Formatter(indent=int_equivalent)
    
    # The bug: floats always become single space instead of being converted to int
    assert formatter.indent == int_formatter.indent, \
        f"Float {float_value} produces '{formatter.indent}' but int {int_equivalent} produces '{int_formatter.indent}'"
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
from bs4.formatter import Formatter

formatter_int = Formatter(indent=0)
formatter_float = Formatter(indent=0.0)

print(f"indent=0 (int): '{formatter_int.indent}'")
print(f"indent=0.0 (float): '{formatter_float.indent}'")

assert formatter_int.indent == ""
assert formatter_float.indent == " "
```

## Why This Is A Bug

The Formatter constructor's docstring states that indent can be "a non-negative integer" but doesn't explicitly handle floats. When a float is passed, it falls through the isinstance checks for int and str, defaulting to a single space. This is inconsistent - floats like 0.0, 2.0, etc. should behave like their integer equivalents (0, 2) for better user experience and consistency.

## Fix

```diff
--- a/bs4/formatter.py
+++ b/bs4/formatter.py
@@ -126,6 +126,10 @@ class Formatter(EntitySubstitution):
             indent = 0
         indent_str: str
         if isinstance(indent, int):
+            if indent < 0:
+                indent = 0
+            indent_str = " " * indent
+        elif isinstance(indent, float):
             if indent < 0:
                 indent = 0
-            indent_str = " " * indent
+            indent_str = " " * int(indent)
         elif isinstance(indent, str):
             indent_str = indent
         else:
```