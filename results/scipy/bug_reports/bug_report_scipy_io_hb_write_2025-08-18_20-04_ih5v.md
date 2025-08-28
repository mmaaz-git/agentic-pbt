# Bug Report: scipy.io.hb_write Cannot Handle Zero Sparse Matrices

**Target**: `scipy.io.hb_write`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

scipy.io.hb_write fails with a ValueError when attempting to write sparse matrices that contain no non-zero elements.

## Property-Based Test

```python
@given(
    matrix=st.one_of(
        st.integers(min_value=2, max_value=10).flatmap(
            lambda cols: st.lists(
                st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
                         min_size=cols, max_size=cols),
                min_size=2, max_size=10
            ).map(lambda x: scipy.sparse.csr_matrix(np.array(x)))
        ),
        st.integers(min_value=2, max_value=20).map(lambda n: scipy.sparse.eye(n, format='csr'))
    )
)
def test_hb_write_read_round_trip(matrix):
    with tempfile.NamedTemporaryFile(suffix='.hb', delete=False) as f:
        filename = f.name
    
    try:
        scipy.io.hb_write(filename, matrix)
        read_matrix = scipy.io.hb_read(filename)
        
        original_dense = matrix.toarray()
        read_dense = read_matrix.toarray()
        
        assert original_dense.shape == read_dense.shape
        np.testing.assert_allclose(original_dense, read_dense, rtol=1e-7, atol=1e-10)
    finally:
        if os.path.exists(filename):
            os.unlink(filename)
```

**Failing input**: `scipy.sparse.csr_matrix([[0.0, 0.0], [0.0, 0.0]])`

## Reproducing the Bug

```python
import scipy.io
import scipy.sparse
import numpy as np

matrix = scipy.sparse.csr_matrix(np.array([[0.0, 0.0], [0.0, 0.0]]))

scipy.io.hb_write('/tmp/test.hb', matrix)
```

## Why This Is A Bug

The Harwell-Boeing format should be able to represent sparse matrices with zero non-zero elements. The error occurs because the code attempts to compute `np.max(indices+1)` on an empty array when there are no non-zero elements. This violates the reasonable expectation that a sparse matrix file format should handle the edge case of a completely zero matrix.

## Fix

The issue is in the HBInfo.from_data() method which doesn't handle the case where a sparse matrix has zero non-zero elements. A fix would involve checking if the matrix has any non-zero elements before attempting operations on the indices array.

```diff
--- a/scipy/io/_harwell_boeing/hb.py
+++ b/scipy/io/_harwell_boeing/hb.py
@@ -76,7 +76,10 @@ class HBInfo:
         pointer_fmt = IntFormat.from_number(np.max(pointer))
-        indices_fmt = IntFormat.from_number(np.max(indices+1))
+        if len(indices) > 0:
+            indices_fmt = IntFormat.from_number(np.max(indices+1))
+        else:
+            indices_fmt = IntFormat(1, 1)
         
         if values.dtype in (np.complex64, np.complex128, np.complex256):
```