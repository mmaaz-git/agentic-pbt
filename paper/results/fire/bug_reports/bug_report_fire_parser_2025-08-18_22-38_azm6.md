# Bug Report: fire.parser Leading Whitespace Parsing Failure

**Target**: `fire.parser.DefaultParseValue`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `DefaultParseValue` function in fire.parser fails to parse values with leading whitespace, incorrectly returning them as strings instead of parsing them to their appropriate Python types.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from fire import parser

@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none()
))
def test_whitespace_invariance(value):
    """Values should parse the same with or without leading/trailing whitespace."""
    string_repr = str(value)
    without_space = parser.DefaultParseValue(string_repr)
    with_space = parser.DefaultParseValue(f'  {string_repr}  ')
    assert without_space == with_space
```

**Failing input**: Any value with leading whitespace, e.g., `' 42'`, `' True'`, `' [1, 2]'`

## Reproducing the Bug

```python
from fire import parser

# Integer parsing fails with leading space
assert parser.DefaultParseValue('42') == 42  # Works
assert parser.DefaultParseValue(' 42') == 42  # Fails - returns ' 42' string

# Boolean parsing fails with leading space  
assert parser.DefaultParseValue('True') is True  # Works
assert parser.DefaultParseValue(' True') is True  # Fails - returns ' True' string

# List parsing fails with leading space
assert parser.DefaultParseValue('[1, 2]') == [1, 2]  # Works
assert parser.DefaultParseValue(' [1, 2]') == [1, 2]  # Fails - returns ' [1, 2]' string
```

## Why This Is A Bug

This violates the expected behavior of a command-line parser where accidental whitespace should not change the interpretation of values. Users who accidentally include leading spaces in their command-line arguments will get strings instead of the expected parsed values, leading to type errors and unexpected behavior in Fire-based CLIs.

The root cause is that `ast.parse()` in 'eval' mode raises a SyntaxError for strings with leading whitespace, causing the parser to fall back to treating the input as a raw string.

## Fix

```diff
--- a/fire/parser.py
+++ b/fire/parser.py
@@ -71,7 +71,14 @@ def DefaultParseValue(value):
   # Note: _LiteralEval will treat '#' as the start of a comment.
   try:
     return _LiteralEval(value)
   except (SyntaxError, ValueError):
-    # If _LiteralEval can't parse the value, treat it as a string.
-    return value
+    # If parsing fails due to whitespace, try stripping and parsing again
+    stripped = value.strip()
+    if stripped != value:
+      try:
+        return _LiteralEval(stripped)
+      except (SyntaxError, ValueError):
+        pass
+    # If all parsing attempts fail, treat it as a string
+    return value
```