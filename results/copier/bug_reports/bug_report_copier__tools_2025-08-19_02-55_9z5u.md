# Bug Report: copier._tools.normalize_git_path UnicodeDecodeError on Non-UTF-8 Input

**Target**: `copier._tools.normalize_git_path`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `normalize_git_path` function crashes with a `UnicodeDecodeError` when processing paths containing certain non-UTF-8 byte sequences, even though the function is designed to handle special Git path encodings.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from copier._tools import normalize_git_path

@given(st.text(min_size=1))
def test_normalize_git_path_handles_quotes(path):
    """normalize_git_path should handle quoted paths."""
    quoted = f'"{path}"'
    result = normalize_git_path(quoted)
    if len(path) >= 2 and path[0] != '"' and path[-1] != '"':
        assert not (result.startswith('"') and result.endswith('"'))
```

**Failing input**: `path='\x80'`

## Reproducing the Bug

```python
from copier._tools import normalize_git_path

path = '\x80'
quoted_path = f'"{path}"'
result = normalize_git_path(quoted_path)
```

## Why This Is A Bug

The `normalize_git_path` function is designed to handle Git paths that may contain special characters and encodings, including octal notation (as documented in its docstring). However, when the input contains certain byte sequences that are not valid UTF-8 (such as `\x80`, `\xFF`, `\xC0`, `\xC1`), the function crashes with a `UnicodeDecodeError` on line 203 when trying to decode as UTF-8.

This violates the expected behavior because:
1. The function should be robust enough to handle various path encodings that Git might produce
2. The function's purpose is to normalize "weird characters" but it fails on certain inputs
3. Git itself can work with filenames containing these byte sequences (in systems that allow them)

## Fix

```diff
--- a/copier/_tools.py
+++ b/copier/_tools.py
@@ -200,7 +200,7 @@ def normalize_git_path(path: str) -> str:
     # Unescape escape characters
     path = path.encode("latin-1", "backslashreplace").decode("unicode-escape")
     # Convert octal to utf8
-    return path.encode("latin-1", "backslashreplace").decode("utf-8")
+    return path.encode("latin-1", "backslashreplace").decode("utf-8", errors="replace")
```