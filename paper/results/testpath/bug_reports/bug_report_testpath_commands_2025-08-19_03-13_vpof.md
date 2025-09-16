# Bug Report: testpath.commands Path Separator Handling

**Target**: `testpath.commands.prepend_to_path` and `remove_from_path`
**Severity**: Low  
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `prepend_to_path` and `remove_from_path` functions fail to properly handle directory names containing the PATH separator character (`:` on Unix, `;` on Windows), causing `remove_from_path` to fail with a ValueError.

## Property-Based Test

```python
from hypothesis import given, assume, strategies as st
import testpath.commands as commands
import os

@given(st.text(min_size=1, max_size=100))
def test_prepend_remove_path_roundtrip(new_dir):
    assume(os.pathsep not in new_dir)
    assume(new_dir.strip())
    
    original_path = os.environ.get('PATH', '')
    
    try:
        commands.prepend_to_path(new_dir)
        modified_path = os.environ['PATH']
        assert modified_path.startswith(new_dir + os.pathsep)
        
        commands.remove_from_path(new_dir)
        restored_path = os.environ.get('PATH', '')
        assert restored_path == original_path
    finally:
        os.environ['PATH'] = original_path
```

**Failing input**: Any string containing `os.pathsep` (`:` on Unix)

## Reproducing the Bug

```python
import os
import testpath.commands as commands

original_path = os.environ.get('PATH', '')
test_dir = f"test{os.pathsep}dir"

try:
    commands.prepend_to_path(test_dir)
    print(f"PATH after prepend: {os.environ['PATH']}")
    
    commands.remove_from_path(test_dir)
except ValueError as e:
    print(f"Bug reproduced: {e}")
finally:
    os.environ['PATH'] = original_path
```

## Why This Is A Bug

When a directory name contains the PATH separator character, `prepend_to_path` adds it to PATH without escaping. Later, `remove_from_path` splits PATH by the separator and cannot find the original directory name because it was split into multiple parts. This breaks the invariant that `remove_from_path` should undo `prepend_to_path`.

## Fix

```diff
--- a/testpath/commands.py
+++ b/testpath/commands.py
@@ -21,10 +21,16 @@ def _make_recording_file(prefix):
     return p
 
 def prepend_to_path(dir):
+    if os.pathsep in dir:
+        raise ValueError(f"Directory name cannot contain path separator {os.pathsep!r}: {dir!r}")
+    if '\x00' in dir:
+        raise ValueError(f"Directory name cannot contain null bytes: {dir!r}")
     os.environ['PATH'] = dir + os.pathsep + os.environ.get('PATH', os.defpath)
 
 def remove_from_path(dir):
+    if os.pathsep in dir:
+        raise ValueError(f"Directory name cannot contain path separator {os.pathsep!r}: {dir!r}")
     path_dirs = os.environ['PATH'].split(os.pathsep)
     path_dirs.remove(dir)
     os.environ['PATH'] = os.pathsep.join(path_dirs)
```