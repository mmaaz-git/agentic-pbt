# Bug Report: rarfile sanitize_filename Idempotence Violation

**Target**: `rarfile.sanitize_filename`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `sanitize_filename` function is not idempotent on Windows paths - applying it twice produces different results than applying it once.

## Property-Based Test

```python
@given(st.text(min_size=0, max_size=255))
@settings(max_examples=1000)
def test_sanitize_filename_idempotence(filename):
    """sanitize_filename should be idempotent: f(f(x)) = f(x)"""
    for is_win32 in [True, False]:
        pathsep = "\\" if is_win32 else "/"
        sanitized_once = rarfile.sanitize_filename(filename, pathsep, is_win32)
        sanitized_twice = rarfile.sanitize_filename(sanitized_once, pathsep, is_win32)
        assert sanitized_once == sanitized_twice
```

**Failing input**: `filename='0/0'` with `is_win32=True`

## Reproducing the Bug

```python
import rarfile

filename = '0/0'
is_win32 = True
pathsep = "\\"

result1 = rarfile.sanitize_filename(filename, pathsep, is_win32)
result2 = rarfile.sanitize_filename(result1, pathsep, is_win32)

print(f"First:  '{filename}' -> '{result1}'")
print(f"Second: '{result1}' -> '{result2}'")
assert result1 == result2, f"Not idempotent: '{result1}' != '{result2}'"
```

## Why This Is A Bug

The function splits paths only on forward slash `/` but joins with the provided path separator. On Windows, it joins with backslash `\`. When run a second time, the backslash is treated as a bad character (per `RC_BAD_CHARS_WIN32`) and replaced with underscore, violating idempotence. This could cause issues when sanitizing already-sanitized filenames.

## Fix

```diff
def sanitize_filename(fname, pathsep, is_win32):
    """Make filename safe for write access.
    """
    if is_win32:
        if len(fname) > 1 and fname[1] == ":":
            fname = fname[2:]
        rc = RC_BAD_CHARS_WIN32
    else:
        rc = RC_BAD_CHARS_UNIX
    if rc.search(fname):
        fname = rc.sub("_", fname)

    parts = []
-    for seg in fname.split("/"):
+    # Split on both forward slash and the current pathsep
+    import re
+    split_pattern = "/" if pathsep != "/" else "/"
+    if pathsep != "/":
+        split_pattern = f"[/{re.escape(pathsep)}]"
+    for seg in re.split(split_pattern, fname):
        if seg in ("", ".", ".."):
            continue
        if is_win32 and seg[-1] in (" ", "."):
            seg = seg[:-1] + "_"
        parts.append(seg)
    return pathsep.join(parts)
```