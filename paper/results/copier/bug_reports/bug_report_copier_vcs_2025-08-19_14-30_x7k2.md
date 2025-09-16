# Bug Report: copier._vcs Functions Crash on Null Characters

**Target**: `copier._vcs` module (functions: `get_repo`, `is_git_repo_root`, `is_git_bundle`)
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

Multiple functions in copier._vcs crash with ValueError when given strings containing null characters ('\x00'), instead of gracefully handling invalid input.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import copier._vcs as vcs

@given(st.text())
@settings(max_examples=2000)
def test_get_repo_no_crash(url):
    """get_repo should not crash on any string input"""
    result = vcs.get_repo(url)
    assert result is None or isinstance(result, str)
```

**Failing input**: `'\x00'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')
import copier._vcs as vcs
from pathlib import Path

# All of these crash with ValueError
vcs.get_repo('\x00')  # ValueError: chdir: embedded null character in path
vcs.is_git_repo_root('\x00')  # ValueError: chdir: embedded null character in path
vcs.is_git_bundle(Path('\x00'))  # ValueError: lstat: embedded null character in path
```

## Why This Is A Bug

These functions are designed to validate and process user-provided URLs and paths. They should handle invalid input gracefully by returning False or None rather than crashing with unhandled exceptions. The null character is a known problematic character in file paths, and the functions should validate input before passing it to OS-level operations.

## Fix

```diff
--- a/copier/_vcs.py
+++ b/copier/_vcs.py
@@ -54,6 +54,9 @@
 
 def is_git_repo_root(path: StrOrPath) -> bool:
     """Indicate if a given path is a git repo root directory."""
+    # Validate path doesn't contain null characters
+    if '\x00' in str(path):
+        return False
     try:
         with local.cwd(Path(path, ".git")):
             return get_git()("rev-parse", "--is-inside-git-dir").strip() == "true"
@@ -83,6 +86,9 @@
 
 def is_git_bundle(path: Path) -> bool:
     """Indicate if a path is a valid git bundle."""
+    # Validate path doesn't contain null characters
+    if '\x00' in str(path):
+        return False
     with suppress(OSError):
         path = path.resolve()
     with TemporaryDirectory(prefix=f"{__name__}.is_git_bundle.") as dirname:
@@ -107,6 +113,10 @@
             - ~/path/to/git/repo
             - ~/path/to/git/repo.bundle
     """
+    # Validate URL doesn't contain null characters
+    if '\x00' in url:
+        return None
+    
     for pattern, replacement in REPLACEMENTS:
         url = re.sub(pattern, replacement, url)
```