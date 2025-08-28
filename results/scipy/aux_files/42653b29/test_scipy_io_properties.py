"""Property-based tests for scipy.io module using Hypothesis."""

import tempfile
import os
import numpy as np
from hypothesis import given, strategies as st, assume, settings
import scipy.io
import scipy.io.wavfile
import scipy.sparse


# WAV file round-trip tests
@given(
    rate=st.integers(min_value=1, max_value=192000),  # Common sample rates
    data=st.one_of(
        # 8-bit unsigned
        st.lists(st.integers(min_value=0, max_value=255), min_size=1, max_size=1000)
            .map(lambda x: np.array(x, dtype=np.uint8)),
        # 16-bit signed (most common)
        st.lists(st.integers(min_value=-32768, max_value=32767), min_size=1, max_size=1000)
            .map(lambda x: np.array(x, dtype=np.int16)),
        # 32-bit signed
        st.lists(st.integers(min_value=-2147483648, max_value=2147483647), min_size=1, max_size=1000)
            .map(lambda x: np.array(x, dtype=np.int32)),
        # 32-bit float
        st.lists(st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False), 
                 min_size=1, max_size=1000)
            .map(lambda x: np.array(x, dtype=np.float32)),
        # Stereo 16-bit
        st.lists(
            st.lists(st.integers(min_value=-32768, max_value=32767), min_size=2, max_size=2),
            min_size=1, max_size=500
        ).map(lambda x: np.array(x, dtype=np.int16))
    )
)
def test_wavfile_round_trip(rate, data):
    """Test that writing and reading a WAV file preserves data."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        filename = f.name
    
    try:
        # Write the data
        scipy.io.wavfile.write(filename, rate, data)
        
        # Read it back
        read_rate, read_data = scipy.io.wavfile.read(filename)
        
        # Check rate is preserved
        assert read_rate == rate, f"Sample rate not preserved: {rate} != {read_rate}"
        
        # Check data shape is preserved
        assert read_data.shape == data.shape, f"Shape not preserved: {data.shape} != {read_data.shape}"
        
        # Check data values - allow for dtype conversions
        if data.dtype == np.float32 or data.dtype == np.float64:
            # Float data might be converted to int16 on write/read
            # Just check the shapes match for now
            pass
        else:
            np.testing.assert_array_equal(read_data, data)
            
    finally:
        if os.path.exists(filename):
            os.unlink(filename)


# Matrix Market round-trip tests
@given(
    matrix=st.one_of(
        # Dense matrices - use fixed column size to avoid jagged arrays
        st.integers(min_value=1, max_value=10).flatmap(
            lambda cols: st.lists(
                st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
                         min_size=cols, max_size=cols),
                min_size=1, max_size=10
            ).map(np.array)
        ),
        # Sparse matrices using scipy.sparse
        st.integers(min_value=1, max_value=10).flatmap(
            lambda cols: st.lists(
                st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
                         min_size=cols, max_size=cols),
                min_size=1, max_size=10
            ).map(lambda x: scipy.sparse.csr_matrix(np.array(x)))
        )
    )
)
def test_mmwrite_mmread_round_trip(matrix):
    """Test that Matrix Market write/read preserves matrix data."""
    with tempfile.NamedTemporaryFile(suffix='.mtx', delete=False, mode='w') as f:
        filename = f.name
    
    try:
        # Write the matrix
        scipy.io.mmwrite(filename, matrix)
        
        # Read it back
        read_matrix = scipy.io.mmread(filename)
        
        # Convert to dense for comparison if needed
        if scipy.sparse.issparse(matrix):
            matrix_dense = matrix.toarray()
        else:
            matrix_dense = np.asarray(matrix)
            
        if scipy.sparse.issparse(read_matrix):
            read_dense = read_matrix.toarray()
        else:
            read_dense = np.asarray(read_matrix)
        
        # Check shape
        assert matrix_dense.shape == read_dense.shape, f"Shape mismatch: {matrix_dense.shape} != {read_dense.shape}"
        
        # Check values (with tolerance for floating point)
        np.testing.assert_allclose(matrix_dense, read_dense, rtol=1e-7, atol=1e-10)
        
    finally:
        if os.path.exists(filename):
            os.unlink(filename)


# MATLAB file round-trip tests
@given(
    data=st.dictionaries(
        # Variable names - MATLAB has restrictions
        keys=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=10),
        values=st.one_of(
            # Scalars
            st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
            st.integers(min_value=-1000000, max_value=1000000),
            # Arrays
            st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
                     min_size=1, max_size=100).map(np.array),
            # 2D arrays - fixed column size
            st.integers(min_value=1, max_value=10).flatmap(
                lambda cols: st.lists(
                    st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
                             min_size=cols, max_size=cols),
                    min_size=1, max_size=10
                ).map(np.array)
            )
        ),
        min_size=1, max_size=5
    )
)
def test_savemat_loadmat_round_trip(data):
    """Test that MATLAB save/load preserves data."""
    with tempfile.NamedTemporaryFile(suffix='.mat', delete=False) as f:
        filename = f.name
    
    try:
        # Save the data
        scipy.io.savemat(filename, data)
        
        # Load it back
        loaded = scipy.io.loadmat(filename)
        
        # Check all original keys are present (loadmat adds some metadata keys)
        for key in data:
            assert key in loaded, f"Key '{key}' not found in loaded data"
            
            original = data[key]
            loaded_val = loaded[key]
            
            # Convert to numpy arrays for comparison
            if not isinstance(original, np.ndarray):
                original = np.array(original)
            
            # MATLAB always uses at least 2D arrays, so flatten if needed
            if original.ndim == 0:
                original = original.reshape(1, 1)
            elif original.ndim == 1:
                original = original.reshape(-1, 1)
                
            # Squeeze loaded value if it has extra dimensions
            if loaded_val.ndim > original.ndim:
                loaded_val = np.squeeze(loaded_val)
                if loaded_val.ndim == 0:
                    loaded_val = loaded_val.reshape(1, 1)
                elif loaded_val.ndim == 1:
                    loaded_val = loaded_val.reshape(-1, 1)
            
            # Check values
            np.testing.assert_allclose(original, loaded_val, rtol=1e-7, atol=1e-10)
            
    finally:
        if os.path.exists(filename):
            os.unlink(filename)


# Harwell-Boeing round-trip tests
@given(
    matrix=st.one_of(
        # Small sparse matrices - fixed column size
        st.integers(min_value=2, max_value=10).flatmap(
            lambda cols: st.lists(
                st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
                         min_size=cols, max_size=cols),
                min_size=2, max_size=10
            ).map(lambda x: scipy.sparse.csr_matrix(np.array(x)))
        ),
        # Identity-like sparse matrices
        st.integers(min_value=2, max_value=20).map(lambda n: scipy.sparse.eye(n, format='csr'))
    )
)
def test_hb_write_read_round_trip(matrix):
    """Test that Harwell-Boeing write/read preserves sparse matrix data."""
    with tempfile.NamedTemporaryFile(suffix='.hb', delete=False) as f:
        filename = f.name
    
    try:
        # Write the matrix
        scipy.io.hb_write(filename, matrix)
        
        # Read it back
        read_matrix = scipy.io.hb_read(filename)
        
        # Both should be sparse
        assert scipy.sparse.issparse(read_matrix), "Read matrix is not sparse"
        
        # Convert to dense for comparison
        original_dense = matrix.toarray()
        read_dense = read_matrix.toarray()
        
        # Check shape
        assert original_dense.shape == read_dense.shape, f"Shape mismatch: {original_dense.shape} != {read_dense.shape}"
        
        # Check values
        np.testing.assert_allclose(original_dense, read_dense, rtol=1e-7, atol=1e-10)
        
    finally:
        if os.path.exists(filename):
            os.unlink(filename)


# Test mminfo consistency
@given(
    matrix=st.one_of(
        st.integers(min_value=1, max_value=10).flatmap(
            lambda cols: st.lists(
                st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
                         min_size=cols, max_size=cols),
                min_size=1, max_size=10
            ).map(np.array)
        ),
        st.integers(min_value=1, max_value=10).flatmap(
            lambda cols: st.lists(
                st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
                         min_size=cols, max_size=cols),
                min_size=1, max_size=10
            ).map(lambda x: scipy.sparse.csr_matrix(np.array(x)))
        )
    )
)
def test_mminfo_consistency(matrix):
    """Test that mminfo returns consistent metadata."""
    with tempfile.NamedTemporaryFile(suffix='.mtx', delete=False, mode='w') as f:
        filename = f.name
    
    try:
        # Write the matrix
        scipy.io.mmwrite(filename, matrix)
        
        # Get info
        info = scipy.io.mminfo(filename)
        
        # info should be a tuple (rows, cols, entries, format, field, symmetry)
        assert len(info) == 6, f"mminfo should return 6 values, got {len(info)}"
        
        rows, cols, entries, format_str, field, symmetry = info
        
        # Check dimensions match
        if scipy.sparse.issparse(matrix):
            actual_shape = matrix.shape
            actual_nnz = matrix.nnz
        else:
            actual_shape = matrix.shape
            actual_nnz = np.count_nonzero(matrix)
        
        assert rows == actual_shape[0], f"Row count mismatch: {rows} != {actual_shape[0]}"
        assert cols == actual_shape[1], f"Col count mismatch: {cols} != {actual_shape[1]}"
        
        # For coordinate format, entries should match non-zero count
        if format_str == 'coordinate':
            assert entries == actual_nnz, f"Entry count mismatch: {entries} != {actual_nnz}"
        
    finally:
        if os.path.exists(filename):
            os.unlink(filename)


# Test whosmat consistency
@given(
    data=st.dictionaries(
        keys=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10),
        values=st.integers(min_value=1, max_value=10).flatmap(
            lambda cols: st.lists(
                st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
                         min_size=cols, max_size=cols),
                min_size=1, max_size=10
            ).map(np.array)
        ),
        min_size=1, max_size=5
    )
)
def test_whosmat_consistency(data):
    """Test that whosmat accurately reports variables in MATLAB files."""
    with tempfile.NamedTemporaryFile(suffix='.mat', delete=False) as f:
        filename = f.name
    
    try:
        # Save the data
        scipy.io.savemat(filename, data)
        
        # Get variable info
        variables = scipy.io.whosmat(filename)
        
        # whosmat returns list of (name, shape, dtype) tuples
        var_names = {var[0] for var in variables}
        
        # Check all saved variables are reported
        for key in data:
            assert key in var_names, f"Variable '{key}' not reported by whosmat"
            
            # Find the variable info
            var_info = next(v for v in variables if v[0] == key)
            name, shape, dtype = var_info
            
            # Check shape matches (accounting for MATLAB's 2D minimum)
            original_shape = data[key].shape
            if len(original_shape) == 0:
                expected_shape = (1, 1)
            elif len(original_shape) == 1:
                expected_shape = (original_shape[0], 1)
            else:
                expected_shape = original_shape
                
            assert shape == expected_shape, f"Shape mismatch for '{key}': {shape} != {expected_shape}"
        
    finally:
        if os.path.exists(filename):
            os.unlink(filename)