# Bug Report: pyximport.pyximport Duplicate PyImportMetaFinder on Multiple install() Calls

**Target**: `pyximport.pyximport.install` and `pyximport.pyximport._have_importers`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `install()` function incorrectly adds duplicate `PyImportMetaFinder` instances to `sys.meta_path` when called multiple times with `pyimport=True`, due to a logic error in the `_have_importers()` function.

## Property-Based Test

```python
from hypothesis import given, strategies as st

@given(
    first_params=st.fixed_dictionaries({
        'pyximport': st.booleans(),
        'pyimport': st.booleans(),
        'language_level': st.one_of(st.none(), st.sampled_from([2, 3]))
    }),
    second_params=st.fixed_dictionaries({
        'pyximport': st.booleans(), 
        'pyimport': st.booleans(),
        'language_level': st.one_of(st.none(), st.sampled_from([2, 3]))
    })
)
def test_multiple_install_idempotence(first_params, second_params):
    """Test that multiple install calls don't duplicate importers"""
    
    initial_meta_path = sys.meta_path.copy()
    
    try:
        py_imp1, pyx_imp1 = pyx.install(**first_params)
        py_imp2, pyx_imp2 = pyx.install(**second_params)
        
        py_importers_count = sum(1 for imp in sys.meta_path 
                                if type(imp).__name__ == 'PyImportMetaFinder')
        
        if first_params['pyimport'] and second_params['pyimport']:
            assert py_importers_count == 1, "Should not duplicate PyImportMetaFinder"
            assert py_imp2 is None, "Second install should return None for existing importer"
            
    finally:
        for imp in sys.meta_path[:]:
            if type(imp).__name__ in ['PyxImportMetaFinder', 'PyImportMetaFinder']:
                sys.meta_path.remove(imp)
```

**Failing input**: `first_params={'pyximport': False, 'pyimport': True, 'language_level': None}, second_params={'pyximport': False, 'pyimport': True, 'language_level': None}`

## Reproducing the Bug

```python
import sys
import pyximport.pyximport as pyx

initial_count = len(sys.meta_path)

py_imp1, pyx_imp1 = pyx.install(pyximport=False, pyimport=True)
py_count1 = sum(1 for imp in sys.meta_path if type(imp).__name__ == 'PyImportMetaFinder')
print(f"After first install: {py_count1} PyImportMetaFinder(s)")

py_imp2, pyx_imp2 = pyx.install(pyximport=False, pyimport=True)
py_count2 = sum(1 for imp in sys.meta_path if type(imp).__name__ == 'PyImportMetaFinder')
print(f"After second install: {py_count2} PyImportMetaFinder(s)")
print(f"Bug: Expected 1, got {py_count2}")
```

## Why This Is A Bug

The `_have_importers()` function incorrectly checks if a `PyImportMetaFinder` exists. It first checks `isinstance(importer, PyxImportMetaFinder)`, but since `PyImportMetaFinder` is not a subclass of `PyxImportMetaFinder` (they are sibling classes), this check always fails for `PyImportMetaFinder` instances. As a result, `has_py_importer` is always `False`, causing `install()` to add duplicate importers to `sys.meta_path`. This violates the idempotence property and can lead to import performance issues and unexpected behavior.

## Fix

The bug is in the `_have_importers()` function. The nested isinstance checks are incorrect since the two classes are not in an inheritance relationship.

```diff
def _have_importers():
    has_py_importer = False
    has_pyx_importer = False
    for importer in sys.meta_path:
-       if isinstance(importer, PyxImportMetaFinder):
-           if isinstance(importer, PyImportMetaFinder):
-               has_py_importer = True
-           else:
-               has_pyx_importer = True
+       if isinstance(importer, PyImportMetaFinder):
+           has_py_importer = True
+       elif isinstance(importer, PyxImportMetaFinder):
+           has_pyx_importer = True

    return has_py_importer, has_pyx_importer
```