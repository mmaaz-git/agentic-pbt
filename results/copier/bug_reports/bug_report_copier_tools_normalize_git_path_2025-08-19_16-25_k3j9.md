# Bug Report: copier._tools.normalize_git_path Crashes on Certain Inputs

**Target**: `copier._tools.normalize_git_path`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `normalize_git_path` function crashes with UnicodeDecodeError when given certain valid string inputs, including strings with non-UTF8 bytes or trailing backslashes.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import copier._tools as tools

@given(path=st.text(min_size=1))
def test_normalize_git_path_utf8(path):
    """normalize_git_path should always return valid UTF-8 strings."""
    if path and path[0] == '"' and path[-1] == '"':
        try:
            normalized = tools.normalize_git_path(path)
            normalized.encode('utf-8')
            assert isinstance(normalized, str)
        except (IndexError, UnicodeDecodeError, UnicodeEncodeError):
            pass
    else:
        normalized = tools.normalize_git_path(path)
        assert isinstance(normalized, str)
```

**Failing input**: `'\x80'` and `'\\'`

## Reproducing the Bug

```python
import copier._tools as tools

# Case 1: Non-UTF8 byte
path1 = '\x80'
result1 = tools.normalize_git_path(path1)  # Raises UnicodeDecodeError

# Case 2: Trailing backslash
path2 = '\\'
result2 = tools.normalize_git_path(path2)  # Raises UnicodeDecodeError
```

## Why This Is A Bug

The function is supposed to normalize Git paths, converting escape sequences to proper UTF-8 strings. However, it fails on certain valid Python string inputs that could represent file paths. The function should either handle these gracefully or validate inputs appropriately.

## Fix

The issue stems from the chained encoding/decoding operations that assume the intermediate results are valid. Here's a potential fix:

```diff
def normalize_git_path(path: str) -> str:
    r"""Convert weird characters returned by Git to normal UTF-8 path strings.
    
    A filename like âñ will be reported by Git as "\\303\\242\\303\\261" (octal notation).
    Similarly, a filename like "<tab>foo\b<lf>ar" will be reported as "\tfoo\\b\nar".
    This can be disabled with `git config core.quotepath off`.
    
    Args:
        path: The Git path to normalize.
    
    Returns:
        str: The normalized Git path.
    """
    # Remove surrounding quotes
    if path[0] == path[-1] == '"':
        path = path[1:-1]
    # Repair double-quotes
    path = path.replace('\\"', '"')
    # Unescape escape characters
-    path = path.encode("latin-1", "backslashreplace").decode("unicode-escape")
+    try:
+        path = path.encode("latin-1", "backslashreplace").decode("unicode-escape")
+    except UnicodeDecodeError:
+        # Handle invalid escape sequences
+        pass
    # Convert octal to utf8
-    return path.encode("latin-1", "backslashreplace").decode("utf-8")
+    try:
+        return path.encode("latin-1", "backslashreplace").decode("utf-8")
+    except UnicodeDecodeError:
+        # Return original path if conversion fails
+        return path
```