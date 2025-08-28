# Bug Report: lxml.isoschematron.stylesheet_params Control Character Crash

**Target**: `lxml.isoschematron.stylesheet_params`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `stylesheet_params` function crashes with ValueError when given strings containing control characters, despite accepting string parameters and not documenting this limitation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import lxml.isoschematron as iso

@given(st.text(min_size=1))
def test_stylesheet_params_accepts_all_strings(text):
    """Test that stylesheet_params handles all valid Python strings."""
    result = iso.stylesheet_params(param=text)
    assert 'param' in result
```

**Failing input**: `'\x1f'` (and other control characters like `'\x00'`, `'\x01'`, `'\x08'`, etc.)

## Reproducing the Bug

```python
import lxml.isoschematron as iso

control_char_string = "\x1f"
result = iso.stylesheet_params(my_param=control_char_string)
```

## Why This Is A Bug

The `stylesheet_params` function is documented to accept string parameters and wrap them with `XSLT.strparam()`. However, it crashes when given valid Python strings containing control characters. The documentation states "If an arg is a string wrap it with XSLT.strparam()" but doesn't mention that some strings will cause crashes. This violates the principle of least surprise and the function's implicit contract.

## Fix

The function should either:
1. Document that control characters are not allowed in string parameters
2. Filter or escape control characters before passing to `XSLT.strparam()`
3. Provide a clearer error message indicating the issue is with the user's input

Here's a potential fix that validates input and provides a better error message:

```diff
--- a/lxml/isoschematron/__init__.py
+++ b/lxml/isoschematron/__init__.py
@@ -91,6 +91,11 @@ def stylesheet_params(**kwargs):
     result = {}
     for key, val in kwargs.items():
         if isinstance(val, basestring):
+            # Check for control characters that XSLT.strparam cannot handle
+            if any(ord(c) < 32 and c not in '\t\n\r' for c in val):
+                raise ValueError(
+                    f"Parameter '{key}' contains control characters which are not "
+                    f"allowed in XSLT parameters. Found in value: {repr(val)}")
             val = _etree.XSLT.strparam(val)
         elif val is None:
             raise TypeError('None not allowed as a stylesheet parameter')
```