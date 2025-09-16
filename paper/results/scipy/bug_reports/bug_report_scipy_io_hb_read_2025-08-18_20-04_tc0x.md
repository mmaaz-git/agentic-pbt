# Bug Report: scipy.io Harwell-Boeing Round-Trip Fails with Denormal Floats

**Target**: `scipy.io.hb_write` and `scipy.io.hb_read`
**Severity**: Medium  
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The Harwell-Boeing format round-trip (write then read) fails when matrices contain very small floating point values (denormal numbers), causing a ValueError during read.

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

**Failing input**: Matrix with values including `1.0` and `-1.360386181804678e-192`

## Reproducing the Bug

```python
import scipy.io
import scipy.sparse
import numpy as np
import tempfile

matrix_data = [[0.0, 0.0, 0.0, 0.0, 0.0],
               [0.0, 0.0, 0.0, 0.0, 0.0],
               [0.0, 0.0, 0.0, 1.0, -1.360386181804678e-192]]

matrix = scipy.sparse.csr_matrix(np.array(matrix_data))

with tempfile.NamedTemporaryFile(suffix='.hb', delete=False) as f:
    filename = f.name

scipy.io.hb_write(filename, matrix)
read_matrix = scipy.io.hb_read(filename)
```

## Why This Is A Bug

The Harwell-Boeing format should support round-trip preservation of sparse matrices with valid floating point values, including denormal numbers. The write operation succeeds but the read operation fails with "string or file could not be read to its end due to unmatched data", violating the expected round-trip property. This indicates that the format writer is not properly formatting very small numbers in a way that the reader can parse.

## Fix

The issue appears to be in how very small floating point numbers are formatted during write. The writer may be using scientific notation that the reader cannot parse correctly, or the field width allocation for values may be insufficient for extreme values. The fix would involve ensuring consistent formatting between writer and reader for edge-case floating point values, possibly by adjusting the precision or format specifiers used when writing denormal numbers.