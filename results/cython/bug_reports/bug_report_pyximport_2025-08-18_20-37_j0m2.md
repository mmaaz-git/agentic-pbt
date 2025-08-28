# Bug Report: pyximport _have_importers() Logic Error Allows Duplicate Importers

**Target**: `pyximport._have_importers()`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_have_importers()` function in pyximport has incorrect logic that fails to detect when a PyImportMetaFinder is already installed, allowing duplicate importers to be added to sys.meta_path.

## Property-Based Test

```python
@given(
    first_pyximport=st.booleans(),
    first_pyimport=st.booleans(),
    second_pyximport=st.booleans(),
    second_pyimport=st.booleans()
)
def test_multiple_install_calls(first_pyximport, first_pyimport, second_pyximport, second_pyimport):
    assume(first_pyximport or first_pyimport)
    assume(second_pyximport or second_pyimport)
    
    with tempfile.TemporaryDirectory() as build_dir1:
        with tempfile.TemporaryDirectory() as build_dir2:
            py1, pyx1 = pyximport.install(
                pyximport=first_pyximport,
                pyimport=first_pyimport,
                build_dir=build_dir1
            )
            
            py2, pyx2 = pyximport.install(
                pyximport=second_pyximport,
                pyimport=second_pyimport,
                build_dir=build_dir2
            )
            
            if first_pyimport and second_pyimport:
                assert py2 is None
```

**Failing input**: `first_pyximport=False, first_pyimport=True, second_pyximport=False, second_pyimport=True`

## Reproducing the Bug

```python
import sys
import tempfile
import pyximport
from pyximport import pyximport as pyx_module

with tempfile.TemporaryDirectory() as build_dir:
    # First install with pyimport=True
    py1, pyx1 = pyximport.install(pyximport=False, pyimport=True, build_dir=build_dir)
    print(f"First install - py1: {py1}")  # Returns PyImportMetaFinder object
    
    # Second install with pyimport=True - should return None but doesn't
    py2, pyx2 = pyximport.install(pyximport=False, pyimport=True, build_dir=build_dir)
    print(f"Second install - py2: {py2}")  # Returns another PyImportMetaFinder object
    
    # Count PyImportMetaFinder instances in sys.meta_path
    count = sum(1 for imp in sys.meta_path if isinstance(imp, pyx_module.PyImportMetaFinder))
    print(f"PyImportMetaFinder count: {count}")  # Prints 2 instead of 1
```

## Why This Is A Bug

The `install()` function is documented to check if importers are already installed and should return None for already-installed importer types. The function relies on `_have_importers()` to detect existing importers, but the logic in `_have_importers()` is flawed: it only checks for PyImportMetaFinder instances that are also PyxImportMetaFinder instances, which is impossible since these are separate classes without inheritance relationship.

## Fix

```diff
--- a/pyximport/pyximport.py
+++ b/pyximport/pyximport.py
@@ -355,13 +355,11 @@ class PyxArgs(object):
 def _have_importers():
     has_py_importer = False
     has_pyx_importer = False
     for importer in sys.meta_path:
-        if isinstance(importer, PyxImportMetaFinder):
-            if isinstance(importer, PyImportMetaFinder):
-                has_py_importer = True
-            else:
-                has_pyx_importer = True
+        if isinstance(importer, PyImportMetaFinder):
+            has_py_importer = True
+        elif isinstance(importer, PyxImportMetaFinder):
+            has_pyx_importer = True
 
     return has_py_importer, has_pyx_importer
```