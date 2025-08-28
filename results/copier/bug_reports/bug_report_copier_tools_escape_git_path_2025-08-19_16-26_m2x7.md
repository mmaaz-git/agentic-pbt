# Bug Report: copier._tools.escape_git_path Not Idempotent

**Target**: `copier._tools.escape_git_path`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `escape_git_path` function is not idempotent - applying it twice to the same input produces different results than applying it once, which violates the expected property for an escaping function.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
import copier._tools as tools

@given(path=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1))
def test_git_path_ascii_roundtrip(path):
    """For ASCII paths, escape should be idempotent."""
    assume('"' not in path)
    assume('\\' not in path)
    
    escaped1 = tools.escape_git_path(path)
    escaped2 = tools.escape_git_path(escaped1)
    assert escaped1 == escaped2
```

**Failing input**: `'#'`

## Reproducing the Bug

```python
import copier._tools as tools

path = '#'
escaped_once = tools.escape_git_path(path)     # Returns '\\#'
escaped_twice = tools.escape_git_path(escaped_once)  # Returns '\\\\\\#'

print(f"Original: {path}")
print(f"Escaped once: {escaped_once}")
print(f"Escaped twice: {escaped_twice}")
print(f"Idempotent? {escaped_once == escaped_twice}")  # False
```

## Why This Is A Bug

An escaping function should be idempotent - escaping an already-escaped string should not change it. This property is important for:
1. Predictable behavior when paths might be processed multiple times
2. Avoiding double-escaping issues in complex pipelines
3. Ensuring path handling is consistent regardless of how many times the function is applied

The current implementation escapes backslashes every time, causing exponential growth in backslashes with repeated applications.

## Fix

The function needs to detect already-escaped sequences and not re-escape them:

```diff
def escape_git_path(path: str) -> str:
    """Escape paths that will be used as literal gitwildmatch patterns.
    
    If the path was returned by a Git command, it should be unescaped completely.
    ``normalize_git_path`` can be used for this purpose.
    
    Args:
        path: The Git path to escape.
    
    Returns:
        str: The escaped Git path.
    """
+    # Check if path is already escaped by looking for escape sequences
+    # If it contains valid escape sequences, return as-is
+    if any(path[i:i+2] in ['\\#', '\\*', '\\?', '\\[', '\\]', '\\\\'] 
+           for i in range(len(path)-1)):
+        # Already escaped, check if fully escaped
+        test_unescaped = GitWildMatchPattern.unescape(path) 
+        if tools.escape_git_path(test_unescaped) == path:
+            return path
+    
    # GitWildMatchPattern.escape does not escape backslashes
    # or trailing whitespace.
    path = path.replace("\\", "\\\\")
    path = GitWildMatchPattern.escape(path)
    return _re_whitespace.sub(
        lambda match: "".join(f"\\{whitespace}" for whitespace in match.group()),
        path,
    )
```