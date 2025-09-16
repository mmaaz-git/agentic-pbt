# Bug Report: copier._tools.normalize_git_path UnicodeDecodeError on Latin-1 Characters

**Target**: `copier._tools.normalize_git_path`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `normalize_git_path` function crashes with a `UnicodeDecodeError` when processing strings containing bytes in the range 0x80-0xFF, which are valid Latin-1 characters but invalid UTF-8 sequences.

## Property-Based Test

```python
import hypothesis.strategies as st
from hypothesis import given
from copier._tools import normalize_git_path

@given(st.text(min_size=2))
def test_normalize_git_path_quoted(path):
    """Test normalize_git_path with quoted paths."""
    quoted_path = f'"{path}"'
    result = normalize_git_path(quoted_path)
    assert not (result.startswith('"') and result.endswith('"'))
```

**Failing input**: `path='0\x80'`

## Reproducing the Bug

```python
from copier._tools import normalize_git_path

input_string = '"0\x80"'
result = normalize_git_path(input_string)
```

## Why This Is A Bug

The function's documentation states it converts "weird characters returned by Git to normal UTF-8 path strings". However, it crashes when given valid string input containing Latin-1 characters (bytes 0x80-0xFF). The function performs the following steps:

1. Removes surrounding quotes
2. Unescapes characters using `unicode-escape` 
3. Attempts to re-encode to Latin-1 and decode as UTF-8

The bug occurs in step 3: characters like `\x80` are valid Latin-1 but form invalid UTF-8 byte sequences, causing the decode to fail. This violates the principle that a string processing function should handle all valid string inputs without crashing.

## Fix

```diff
--- a/copier/_tools.py
+++ b/copier/_tools.py
@@ -200,5 +200,9 @@ def normalize_git_path(path: str) -> str:
     # Unescape escape characters
     path = path.encode("latin-1", "backslashreplace").decode("unicode-escape")
     # Convert octal to utf8
-    return path.encode("latin-1", "backslashreplace").decode("utf-8")
+    try:
+        return path.encode("latin-1", "backslashreplace").decode("utf-8")
+    except UnicodeDecodeError:
+        # If the result isn't valid UTF-8, return the partially processed string
+        return path
```

Alternative fix: Use `errors='replace'` or `errors='ignore'` parameter in the decode call to handle invalid UTF-8 sequences gracefully:

```diff
--- a/copier/_tools.py
+++ b/copier/_tools.py
@@ -200,5 +200,5 @@ def normalize_git_path(path: str) -> str:
     # Unescape escape characters
     path = path.encode("latin-1", "backslashreplace").decode("unicode-escape")
     # Convert octal to utf8
-    return path.encode("latin-1", "backslashreplace").decode("utf-8")
+    return path.encode("latin-1", "backslashreplace").decode("utf-8", errors="replace")
```