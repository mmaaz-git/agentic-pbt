# Bug Report: pyramid.path FSAssetDescriptor Inconsistent Null Byte Handling

**Target**: `pyramid.path.FSAssetDescriptor`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

FSAssetDescriptor methods handle paths containing null bytes inconsistently - some methods gracefully handle invalid paths while `listdir()` crashes with a ValueError.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.path import FSAssetDescriptor

@given(st.text(min_size=1, max_size=100))
def test_fs_descriptor_methods_dont_crash(path):
    """FSAssetDescriptor methods shouldn't crash on any input"""
    descriptor = FSAssetDescriptor(path)
    
    # These should not crash
    _ = descriptor.abspath()
    _ = descriptor.exists()
    _ = descriptor.isdir()
    
    # listdir might fail but shouldn't crash the process
    try:
        _ = descriptor.listdir()
    except (OSError, IOError):
        pass  # Expected for non-directories
```

**Failing input**: `'\x00'`

## Reproducing the Bug

```python
from pyramid.path import FSAssetDescriptor

path_with_null = "test\x00file"
descriptor = FSAssetDescriptor(path_with_null)

# These methods handle null bytes gracefully
print(descriptor.exists())  # Returns False
print(descriptor.isdir())   # Returns False  
print(descriptor.abspath())  # Returns truncated path

# This method crashes
descriptor.listdir()  # ValueError: listdir: embedded null character in path
```

## Why This Is A Bug

FSAssetDescriptor methods should handle invalid paths consistently. Currently:
- `exists()` and `isdir()` return False for paths with null bytes (graceful)
- `abspath()` silently truncates at the null byte
- `listdir()` raises a ValueError

This inconsistency means users cannot reliably handle arbitrary paths without catching specific exceptions for certain methods.

## Fix

```diff
--- a/pyramid/path.py
+++ b/pyramid/path.py
@@ -439,7 +439,11 @@ class FSAssetDescriptor:
         return os.path.isdir(self.path)
 
     def listdir(self):
-        return os.listdir(self.path)
+        try:
+            return os.listdir(self.path)
+        except (ValueError, OSError):
+            # Handle invalid paths like null bytes consistently
+            return []
 
     def exists(self):
         return os.path.exists(self.path)
```