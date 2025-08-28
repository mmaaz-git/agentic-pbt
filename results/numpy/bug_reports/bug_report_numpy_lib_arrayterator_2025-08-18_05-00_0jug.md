# Bug Report: numpy.lib.Arrayterator Integer Indexing Dimension Preservation

**Target**: `numpy.lib.Arrayterator`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Arrayterator violates NumPy's fundamental indexing contract: integer indexing does not reduce dimensionality as expected, instead preserving dimensions with size 1.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import numpy as np
from numpy.lib import Arrayterator

@given(
    shape=st.lists(st.integers(2, 10), min_size=2, max_size=3),
    buf_size=st.integers(1, 50)
)
@settings(max_examples=100)
def test_arrayterator_indexing_consistency(shape, buf_size):
    arr = np.arange(np.prod(shape)).reshape(shape)
    iterator = Arrayterator(arr, buf_size=buf_size)
    
    indexed = iterator[0]
    expected_shape = shape[1:]
    
    assert indexed.shape == expected_shape, \
        f"Integer indexing shape mismatch: got {indexed.shape}, expected {expected_shape}"
```

**Failing input**: `shape=[2, 2], buf_size=1`

## Reproducing the Bug

```python
import numpy as np
from numpy.lib import Arrayterator

arr = np.array([[0, 1], [2, 3]])
iterator = Arrayterator(arr, buf_size=1)

arr_indexed = arr[0]
iter_indexed = iterator[0]

print(f"arr[0].shape: {arr_indexed.shape}")
print(f"iterator[0].shape: {iter_indexed.shape}")
print(f"Expected: {arr_indexed.shape}, Got: {iter_indexed.shape}")
```

## Why This Is A Bug

NumPy arrays follow a fundamental convention: integer indexing reduces dimensionality. When indexing `arr[0]` on a 2D array, the result should be 1D. Arrayterator breaks this convention by converting integer indices to slices, preserving all dimensions. This violates the principle of least surprise and breaks compatibility with code expecting standard NumPy indexing behavior.

## Fix

```diff
--- a/numpy/lib/_arrayterator_impl.py
+++ b/numpy/lib/_arrayterator_impl.py
@@ -109,11 +109,14 @@ class Arrayterator:
         for slice_ in index:
             if slice_ is Ellipsis:
                 fixed.extend([slice(None)] * (dims - length + 1))
                 length = len(fixed)
             elif isinstance(slice_, int):
-                fixed.append(slice(slice_, slice_ + 1, 1))
+                # Mark integer indices for dimension reduction
+                fixed.append(('int', slice_))
             else:
                 fixed.append(slice_)
+        
+        # Convert integer markers back and track which dimensions to squeeze
+        squeeze_dims = []
+        for i, item in enumerate(fixed):
+            if isinstance(item, tuple) and item[0] == 'int':
+                fixed[i] = slice(item[1], item[1] + 1, 1)
+                squeeze_dims.append(i)
+        
         index = tuple(fixed)
         if len(index) < dims:
             index += (slice(None),) * (dims - len(index))
 
         # Return a new arrayterator object.
         out = self.__class__(self.var, self.buf_size)
         for i, (start, stop, step, slice_) in enumerate(
                 zip(self.start, self.stop, self.step, index)):
             out.start[i] = start + (slice_.start or 0)
             out.step[i] = step * (slice_.step or 1)
             out.stop[i] = start + (slice_.stop or stop - start)
             out.stop[i] = min(stop, out.stop[i])
+        
+        # Reduce shape for integer-indexed dimensions
+        new_shape = []
+        for i, s in enumerate(out.shape):
+            if i not in squeeze_dims:
+                new_shape.append(s)
+        out.shape = tuple(new_shape) if new_shape else ()
+        
         return out
```