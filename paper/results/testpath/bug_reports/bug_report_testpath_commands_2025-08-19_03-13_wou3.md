# Bug Report: testpath.commands Null Byte Handling

**Target**: `testpath.commands.prepend_to_path`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `prepend_to_path` function crashes with a generic ValueError when given a directory name containing a null byte, instead of handling the invalid input gracefully.

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

**Failing input**: `'\x00'`

## Reproducing the Bug

```python
import os
import testpath.commands as commands

original_path = os.environ.get('PATH', '')
try:
    commands.prepend_to_path('\x00')
except ValueError as e:
    print(f"Bug reproduced: {e}")
finally:
    os.environ['PATH'] = original_path
```

## Why This Is A Bug

The function doesn't validate its input before attempting to modify the PATH environment variable. When given a null byte, it crashes with a generic "embedded null byte" error from the OS level, rather than providing clear error handling or documentation about this limitation.

## Fix

```diff
--- a/testpath/commands.py
+++ b/testpath/commands.py
@@ -21,6 +21,9 @@ def _make_recording_file(prefix):
     return p
 
 def prepend_to_path(dir):
+    if '\x00' in dir:
+        raise ValueError(f"Directory name cannot contain null bytes: {dir!r}")
+    if os.pathsep in dir:
+        raise ValueError(f"Directory name cannot contain path separator {os.pathsep!r}: {dir!r}")
     os.environ['PATH'] = dir + os.pathsep + os.environ.get('PATH', os.defpath)
```