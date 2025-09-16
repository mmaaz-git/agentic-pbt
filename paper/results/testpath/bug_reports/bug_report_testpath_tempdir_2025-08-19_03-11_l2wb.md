# Bug Report: testpath.tempdir AttributeError in cleanup when file opening fails

**Target**: `testpath.tempdir.NamedFileInTemporaryDirectory`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

NamedFileInTemporaryDirectory's cleanup method raises AttributeError when __init__ fails after creating the temporary directory but before successfully opening the file.

## Property-Based Test

```python
from hypothesis import given, strategies as st

@given(mode=st.sampled_from(['r', 'rb']))
def test_cleanup_bug_with_read_mode(mode):
    """Test that cleanup doesn't fail when file opening fails."""
    try:
        with testpath.tempdir.NamedFileInTemporaryDirectory('testfile.txt', mode=mode) as f:
            pass
    except FileNotFoundError:
        pass  # Expected - file doesn't exist for read mode
```

**Failing input**: `mode='r'`

## Reproducing the Bug

```python
from testpath.tempdir import NamedFileInTemporaryDirectory

try:
    with NamedFileInTemporaryDirectory('test.txt', mode='r') as f:
        pass
except FileNotFoundError:
    print("FileNotFoundError caught (expected)")
```

## Why This Is A Bug

The __init__ method creates self._tmpdir before attempting to open the file. If the file opening fails (e.g., mode='r' on non-existent file), self.file is never set. However, the cleanup method unconditionally tries to close self.file, causing AttributeError. This results in resource cleanup failures and error messages during garbage collection.

## Fix

```diff
--- a/testpath/tempdir.py
+++ b/testpath/tempdir.py
@@ -34,7 +34,8 @@ class NamedFileInTemporaryDirectory(object):
         self.file = open(path, mode, bufsize)
 
     def cleanup(self):
-        self.file.close()
+        if hasattr(self, 'file'):
+            self.file.close()
         self._tmpdir.cleanup()
 
     __del__ = cleanup
```