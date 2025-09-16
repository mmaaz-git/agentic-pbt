# Bug Report: requests.utils.super_len Inconsistent String Length Calculation

**Target**: `requests.utils.super_len`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `super_len()` function returns byte length instead of character length for strings when using urllib3 2.x+, making it inconsistent with Python's built-in `len()` function and its own behavior for other types.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import requests.utils

@given(st.text())
def test_super_len_string_length(s):
    """Test that super_len returns same length as len() for strings."""
    length = requests.utils.super_len(s)
    expected_length = len(s)
    assert length == expected_length
```

**Failing input**: `'\x80'`

## Reproducing the Bug

```python
import requests.utils

s = '\x80'
print(f"String: {repr(s)}")
print(f"len(s): {len(s)}")
print(f"super_len(s): {requests.utils.super_len(s)}")

assert requests.utils.super_len(s) == len(s)
```

## Why This Is A Bug

The `super_len()` function is meant to be a enhanced version of `len()` that can handle file-like objects. For all standard Python types (lists, tuples, dicts, bytes), it returns the same value as `len()`. However, for strings with non-ASCII characters when using urllib3 2.x+, it returns the UTF-8 byte length instead of the character count.

This inconsistency violates the principle of least surprise - a function named `super_len` should behave like `len()` for standard types. While returning byte length might be correct for HTTP Content-Length headers, the function itself should maintain consistent semantics.

## Fix

The issue is in the string handling logic that converts strings to UTF-8 bytes when `is_urllib3_1` is False:

```diff
--- a/requests/utils.py
+++ b/requests/utils.py
@@ -557,11 +557,6 @@ def super_len(o):
     total_length = None
     current_position = 0
 
-    if not is_urllib3_1 and isinstance(o, str):
-        # urllib3 2.x+ treats all strings as utf-8 instead
-        # of latin-1 (iso-8859-1) like http.client.
-        o = o.encode("utf-8")
-
     if hasattr(o, "__len__"):
         total_length = len(o)
```

Alternatively, if the byte-length behavior is intentional for Content-Length calculation, the function should be renamed or documented clearly to indicate it returns byte length for strings, not character length.