# Bug Report: pyramid.asset Trailing Slash Path Recognition Bug

**Target**: `pyramid.asset.asset_spec_from_abspath`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `asset_spec_from_abspath` function fails to correctly recognize package directories as part of the package when there's no trailing slash, and fails entirely when `package_path` returns a path with a trailing slash.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pyramid.asset as asset

@given(
    st.text(alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')), min_size=1, max_size=10),
    st.booleans()
)
def test_asset_spec_from_abspath_package_dir_bug(pkg_name, with_trailing_slash):
    """Property: The package directory itself should be recognized as part of the package"""
    
    if pkg_name == '__main__':
        return
    
    class MockPackage:
        def __init__(self, name):
            self.__name__ = name
    
    package = MockPackage(pkg_name)
    base_path = f'/test/{pkg_name}'
    
    original_package_path = asset.package_path
    original_package_name = asset.package_name
    
    try:
        asset.package_path = lambda p: base_path
        asset.package_name = lambda p: p.__name__
        
        if with_trailing_slash:
            abspath = base_path + '/'
        else:
            abspath = base_path
        
        result = asset.asset_spec_from_abspath(abspath, package)
        
        # Bug: inconsistent behavior based on trailing slash
        if with_trailing_slash:
            assert result == f"{pkg_name}:"  # Works correctly
        else:
            assert result == abspath  # Bug: returns absolute path instead of asset spec
            
    finally:
        asset.package_path = original_package_path
        asset.package_name = original_package_name
```

**Failing input**: `pkg_name='a', with_trailing_slash=False`

## Reproducing the Bug

```python
import os
import pyramid.asset as asset
from pyramid.path import package_path, package_name

class TestPackage:
    __name__ = 'testpkg'

package = TestPackage()
original_package_path = asset.package_path
original_package_name = asset.package_name

asset.package_path = lambda p: '/base/testpkg'
asset.package_name = lambda p: p.__name__

# BUG 1: Package directory without trailing slash is not recognized
abspath1 = '/base/testpkg'
result1 = asset.asset_spec_from_abspath(abspath1, package)
assert result1 == '/base/testpkg'  # Returns absolute path instead of 'testpkg:'

# BUG 2: If package_path returns path with trailing slash, files aren't recognized
asset.package_path = lambda p: '/base/testpkg/'
abspath2 = '/base/testpkg/file.txt'
result2 = asset.asset_spec_from_abspath(abspath2, package)
assert result2 == '/base/testpkg/file.txt'  # Returns absolute path instead of 'testpkg:file.txt'

asset.package_path = original_package_path
asset.package_name = original_package_name
```

## Why This Is A Bug

The function's logic for determining if a path is within a package is flawed:
1. It unconditionally appends `os.path.sep` to the package path, creating issues when comparing paths
2. This causes the package directory itself (without trailing slash) to not be recognized as part of the package
3. If `package_path` already has a trailing slash, the double slash breaks path recognition entirely

This violates the expected behavior that any path within or equal to the package directory should be recognized as part of the package and converted to an asset specification.

## Fix

```diff
--- a/pyramid/asset.py
+++ b/pyramid/asset.py
@@ -21,8 +21,12 @@ def asset_spec_from_abspath(abspath, package):
     """Try to convert an absolute path to a resource in a package to
     a resource specification if possible; otherwise return the
     absolute path."""
     if getattr(package, '__name__', None) == '__main__':
         return abspath
-    pp = package_path(package) + os.path.sep
-    if abspath.startswith(pp):
+    pp = package_path(package)
+    # Normalize both paths to handle trailing slashes consistently
+    pp_normalized = os.path.normpath(pp)
+    abspath_normalized = os.path.normpath(abspath)
+    
+    if abspath_normalized == pp_normalized:
+        return '%s:' % package_name(package)
+    elif abspath_normalized.startswith(pp_normalized + os.path.sep):
-        relpath = abspath[len(pp) :]
+        relpath = abspath_normalized[len(pp_normalized) + 1:]
         return '%s:%s' % (
             package_name(package),
             relpath.replace(os.path.sep, '/'),
         )
     return abspath
```