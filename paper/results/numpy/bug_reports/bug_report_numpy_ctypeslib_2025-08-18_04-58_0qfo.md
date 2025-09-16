# Bug Report: numpy.ctypeslib F-Contiguous Arrays Incorrectly Rejected

**Target**: `numpy.ctypeslib.as_ctypes`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `as_ctypes` function incorrectly rejects F-contiguous (Fortran-order) arrays as "strided arrays not supported", even though F-contiguous arrays are valid contiguous arrays that should be supported.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import numpy as np

@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=4, max_size=20))
@settings(max_examples=500)
def test_f_contiguous_round_trip(values):
    """Test F-contiguous array handling"""
    size = len(values)
    if size < 4:
        return
    
    rows = 2
    cols = size // rows
    values = values[:rows*cols]
    
    # Create F-contiguous array
    arr = np.array(values, dtype=np.int32).reshape((rows, cols), order='F')
    assert arr.flags['F_CONTIGUOUS']
    
    # Convert to ctypes - THIS FAILS BUT SHOULDN'T
    ct = np.ctypeslib.as_ctypes(arr)
    
    # Convert back
    arr2 = np.ctypeslib.as_array(ct)
    
    # Check data is preserved
    assert np.array_equal(arr, arr2)
```

**Failing input**: `values=[0, 0, 0, 0]` (any values will fail)

## Reproducing the Bug

```python
import numpy as np

# Create F-contiguous array
arr_f = np.array([[1, 2], [3, 4]], dtype=np.int32, order='F')
print('F-contiguous array is contiguous:', arr_f.flags['F_CONTIGUOUS'])

# This should work but raises TypeError
try:
    ct = np.ctypeslib.as_ctypes(arr_f)
    print('Success')
except TypeError as e:
    print('Error:', e)
    
# C-contiguous arrays work fine
arr_c = np.array([[1, 2], [3, 4]], dtype=np.int32, order='C')
ct_c = np.ctypeslib.as_ctypes(arr_c)
print('C-contiguous works fine')
```

## Why This Is A Bug

F-contiguous arrays are valid contiguous arrays, just with a different memory layout (column-major instead of row-major). The `as_ctypes` function checks `if ai["strides"]:` to reject strided arrays, but this check is too broad:

1. C-contiguous arrays have `strides=None` in their `__array_interface__`
2. F-contiguous arrays have `strides=(row_bytes, col_bytes)` even though they're contiguous
3. Actually non-contiguous arrays also have strides

The function should check if the array is actually non-contiguous (neither C nor F contiguous) rather than just checking for the presence of strides.

## Fix

```diff
--- a/numpy/ctypeslib/_ctypeslib.py
+++ b/numpy/ctypeslib/_ctypeslib.py
@@ -586,8 +586,13 @@ def as_ctypes(obj):
 
     """
     ai = obj.__array_interface__
-    if ai["strides"]:
-        raise TypeError("strided arrays not supported")
+    # Check if array is actually non-contiguous
+    # F-contiguous arrays have strides but are still contiguous
+    if hasattr(obj, 'flags'):
+        if not (obj.flags['C_CONTIGUOUS'] or obj.flags['F_CONTIGUOUS']):
+            raise TypeError("non-contiguous arrays not supported")
+    elif ai["strides"]:
+        raise TypeError("strided arrays not supported")
     if ai["version"] != 3:
         raise TypeError("only __array_interface__ version 3 supported")
     addr, readonly = ai["data"]
```