# Bug Report: pyramid.util.bytes_ Encoding Failure with Non-Latin-1 Characters

**Target**: `pyramid.util.bytes_`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `bytes_` function in pyramid.util fails with a UnicodeEncodeError when given Unicode characters outside the Latin-1 range (codepoint > 255), but this limitation is not documented.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.util import bytes_

@given(st.text())
def test_bytes_conversion(text):
    """bytes_ should convert str to bytes, leave bytes unchanged."""
    result = bytes_(text)
    assert isinstance(result, bytes)
    assert result == text.encode('latin-1')
```

**Failing input**: `'Ā'` (character with codepoint 256)

## Reproducing the Bug

```python
from pyramid.util import bytes_

text = 'Ā'  # Character with codepoint 256
result = bytes_(text)  # Raises UnicodeEncodeError
```

## Why This Is A Bug

The function's docstring states: "If ``s`` is an instance of ``str``, return ``s.encode(encoding, errors)``" but doesn't mention that the default encoding is 'latin-1' which only supports characters with codepoints 0-255. This is a contract violation because:

1. The function accepts any string but silently uses a restrictive encoding
2. Users may reasonably expect UTF-8 encoding by default in modern Python
3. The pyramid.session module uses this function to process cookie values, which could contain any Unicode text

This could cause unexpected failures in production when session data contains non-Latin-1 characters.

## Fix

Either update the documentation to clearly state the Latin-1 limitation, or change the default encoding to UTF-8:

```diff
-def bytes_(s, encoding='latin-1', errors='strict'):
-    """If ``s`` is an instance of ``str``, return
-    ``s.encode(encoding, errors)``, otherwise return ``s``"""
+def bytes_(s, encoding='utf-8', errors='strict'):
+    """If ``s`` is an instance of ``str``, return
+    ``s.encode(encoding, errors)``, otherwise return ``s``
+    
+    Note: Default encoding is UTF-8. For backwards compatibility,
+    you can specify encoding='latin-1'."""
     if isinstance(s, str):
         return s.encode(encoding, errors)
     return s
```

Alternatively, keep latin-1 but update documentation:

```diff
 def bytes_(s, encoding='latin-1', errors='strict'):
-    """If ``s`` is an instance of ``str``, return
-    ``s.encode(encoding, errors)``, otherwise return ``s``"""
+    """If ``s`` is an instance of ``str``, return
+    ``s.encode(encoding, errors)``, otherwise return ``s``
+    
+    Warning: Default encoding is 'latin-1' which only supports
+    characters with codepoints 0-255. Use encoding='utf-8' for
+    full Unicode support."""
     if isinstance(s, str):
         return s.encode(encoding, errors)
     return s
```