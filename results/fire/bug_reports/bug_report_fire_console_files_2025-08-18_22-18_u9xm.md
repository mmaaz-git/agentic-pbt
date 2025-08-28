# Bug Report: fire.console.files Cross-Platform Path Separator Handling

**Target**: `fire.console.files.FindExecutableOnPath`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

`FindExecutableOnPath` fails to reject executables containing backslash path separators on Unix systems, violating its documented contract that executables "must not have a path."

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from fire.console import files

@given(st.text(min_size=1).filter(lambda x: '/' in x or '\\' in x))
def test_find_executable_with_path_raises(executable):
    """Test that FindExecutableOnPath raises ValueError when executable has a path."""
    with pytest.raises(ValueError, match="must not have a path"):
        files.FindExecutableOnPath(executable)
```

**Failing input**: `'\\'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
from fire.console import files

executable = '\\'
try:
    result = files.FindExecutableOnPath(executable)
    print(f"No error raised for '{executable}', returned: {result}")
except ValueError as e:
    print(f"ValueError raised: {e}")
```

## Why This Is A Bug

The function's docstring and error message state that the executable "must not have a path," but the implementation only checks using `os.path.dirname()`. On Unix systems, this function doesn't recognize backslashes as path separators, allowing inputs like `'\'`, `'foo\bar'`, and `'\foo'` to pass validation when they clearly contain path components.

This creates platform-inconsistent behavior where the same input may be accepted or rejected depending on the operating system, violating the principle of least surprise and the function's documented contract.

## Fix

```diff
--- a/fire/console/files.py
+++ b/fire/console/files.py
@@ -98,7 +98,8 @@ def FindExecutableOnPath(executable, path=None, pathext=None,
     raise ValueError('FindExecutableOnPath({0},...) failed because first '
                      'argument must not have an extension.'.format(executable))
 
-  if os.path.dirname(executable):
+  # Check for any path separators (both forward and backward slashes)
+  if os.path.dirname(executable) or '/' in executable or '\\' in executable:
     raise ValueError('FindExecutableOnPath({0},...) failed because first '
                      'argument must not have a path.'.format(executable))
```