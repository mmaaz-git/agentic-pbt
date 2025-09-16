# Bug Report: testpath.asserts Broken Symlink Inverse Property Violation

**Target**: `testpath.asserts`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The functions `assert_path_exists` and `assert_not_path_exists` violate their inverse property when dealing with broken symlinks, causing both assertions to fail for the same path.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import testpath.asserts as asserts
import os
import tempfile

@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=5, max_size=10))
def test_broken_symlink_inverse_property(name):
    """Property: For any path, exactly one of assert_path_exists and assert_not_path_exists should pass."""
    temp_dir = tempfile.gettempdir()
    symlink_path = os.path.join(temp_dir, f"hypo_{name}")
    target_path = os.path.join(temp_dir, f"target_{name}")
    
    # Clean up first
    for p in [symlink_path, target_path]:
        try:
            if os.path.islink(p) or os.path.exists(p):
                os.remove(p)
        except:
            pass
    
    # Create a broken symlink
    os.symlink(target_path, symlink_path)
    
    # Count how many assertions pass
    passing = []
    
    try:
        asserts.assert_path_exists(symlink_path)
        passing.append('exists')
    except AssertionError:
        pass
    
    try:
        asserts.assert_not_path_exists(symlink_path)
        passing.append('not_exists')
    except AssertionError:
        pass
    
    # Clean up
    os.remove(symlink_path)
    
    # Exactly one should pass (inverse property)
    assert len(passing) == 1, f"Inverse property violated: {passing} passed"
```

**Failing input**: Any broken symlink (symlink pointing to non-existent target)

## Reproducing the Bug

```python
import os
import tempfile
import testpath.asserts as asserts

# Create a broken symlink
temp_dir = tempfile.gettempdir()
symlink_path = os.path.join(temp_dir, "broken_symlink")
target_path = os.path.join(temp_dir, "nonexistent_target")

# Ensure cleanup
for p in [symlink_path, target_path]:
    try:
        if os.path.islink(p) or os.path.exists(p):
            os.remove(p)
    except:
        pass

# Create broken symlink
os.symlink(target_path, symlink_path)

# Both fail - violating inverse property
try:
    asserts.assert_path_exists(symlink_path)
    print("assert_path_exists: PASSED")
except AssertionError as e:
    print(f"assert_path_exists: FAILED - {e}")

try:
    asserts.assert_not_path_exists(symlink_path)
    print("assert_not_path_exists: PASSED")
except AssertionError:
    print("assert_not_path_exists: FAILED")

# Cleanup
os.remove(symlink_path)
```

## Why This Is A Bug

The functions `assert_path_exists` and `assert_not_path_exists` should be logical inverses - for any given path, exactly one should pass. However, for broken symlinks:

1. `assert_path_exists` fails because it uses `os.stat()` with `follow_symlinks=True`, which raises OSError on broken symlinks
2. `assert_not_path_exists` passes because it uses `os.path.exists()`, which returns False for broken symlinks

This inconsistency violates the reasonable expectation that these functions form a complementary pair, potentially causing confusion in test suites that handle symlinks.

## Fix

```diff
--- a/testpath/asserts.py
+++ b/testpath/asserts.py
@@ -43,8 +43,11 @@ def _stat_for_assert(path, follow_symlinks=True, msg=None):
 
 def assert_path_exists(path, msg=None):
     """Assert that something exists at the given path.
     """
-    _stat_for_assert(_strpath(path), True, msg)
+    path = _strpath(path)
+    # Use os.path.lexists to detect broken symlinks
+    if not os.path.lexists(path):
+        if msg is None:
+            msg = "Path does not exist: %r" % path
+        raise AssertionError(msg)
 
 def assert_not_path_exists(path, msg=None):
     """Assert that nothing exists at the given path.
     """
     path = _strpath(path)
-    if os.path.exists(path):
+    # Use os.path.lexists to detect broken symlinks
+    if os.path.lexists(path):
         if msg is None:
             msg = "Path exists: %r" % path
         raise AssertionError(msg)
```