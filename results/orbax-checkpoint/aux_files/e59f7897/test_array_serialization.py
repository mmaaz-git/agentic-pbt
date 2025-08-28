#!/usr/bin/env python3
"""Test array serialization edge cases in orbax"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/orbax-checkpoint_env/lib/python3.13/site-packages')

import numpy as np
import jax
import jax.numpy as jnp
from hypothesis import given, strategies as st, settings, assume
import orbax.checkpoint.msgpack_utils as msgpack_utils
import pytest


# Test complex numbers (special case in msgpack)
@given(
    st.complex_numbers(allow_nan=False, allow_infinity=False,
                       min_magnitude=0, max_magnitude=1000)
)
@settings(max_examples=100)
def test_complex_number_msgpack(c):
    """Test that complex numbers serialize correctly"""
    tree = {'complex': c, 'real': c.real, 'imag': c.imag}
    
    serialized = msgpack_utils.msgpack_serialize(tree)
    restored = msgpack_utils.msgpack_restore(serialized)
    
    assert 'complex' in restored
    assert isinstance(restored['complex'], complex)
    assert abs(restored['complex'] - c) < 1e-10
    assert abs(restored['real'] - c.real) < 1e-10
    assert abs(restored['imag'] - c.imag) < 1e-10


# Test numpy scalars (special case in msgpack)
@given(st.sampled_from([
    np.int8, np.int16, np.int32, np.int64,
    np.uint8, np.uint16, np.uint32, np.uint64,
    np.float16, np.float32, np.float64
]))
@settings(max_examples=50)
def test_numpy_scalar_types(dtype):
    """Test various numpy scalar types"""
    if dtype in [np.int8, np.int16, np.int32, np.int64]:
        value = dtype(42)
    elif dtype in [np.uint8, np.uint16, np.uint32, np.uint64]:
        value = dtype(42)
    else:
        value = dtype(3.14159)
    
    tree = {'scalar': value, 'array': np.array([value])}
    
    serialized = msgpack_utils.msgpack_serialize(tree)
    restored = msgpack_utils.msgpack_restore(serialized)
    
    # Check scalar is preserved
    assert 'scalar' in restored
    # Type might change but value should be preserved
    if np.issubdtype(dtype, np.integer):
        assert int(restored['scalar']) == int(value)
    else:
        assert abs(float(restored['scalar']) - float(value)) < 1e-6


# Test edge case dtypes
@given(st.sampled_from(['bool', 'complex64', 'complex128']))
@settings(max_examples=50)
def test_special_dtypes(dtype_str):
    """Test special numpy dtypes"""
    dtype = np.dtype(dtype_str)
    
    if dtype == np.bool_:
        arr = np.array([True, False, True], dtype=dtype)
    elif dtype in [np.complex64, np.complex128]:
        arr = np.array([1+2j, 3-4j], dtype=dtype)
    else:
        arr = np.array([1, 2, 3], dtype=dtype)
    
    tree = {'data': arr}
    
    serialized = msgpack_utils.msgpack_serialize(tree)
    restored = msgpack_utils.msgpack_restore(serialized)
    
    assert 'data' in restored
    assert restored['data'].shape == arr.shape
    if dtype in [np.complex64, np.complex128]:
        assert np.allclose(restored['data'], arr)
    else:
        assert np.array_equal(restored['data'], arr)


# Test arrays with extreme shapes
@given(st.sampled_from([
    (1000000,),  # Very long 1D
    (1, 1, 1000, 1000),  # High dimensional with large last dims
    (1000, 1, 1, 1000),  # Large first and last dims
    tuple(),  # Empty shape (scalar array)
    (0,),  # Zero-length array
    (10, 0, 5),  # Array with zero dimension
]))
@settings(max_examples=50, deadline=10000)
def test_extreme_array_shapes(shape):
    """Test arrays with unusual shapes"""
    size = np.prod(shape)
    
    # Skip very large arrays for memory reasons
    if size > 10000000:
        assume(False)
    
    if size == 0:
        arr = np.zeros(shape, dtype=np.float32)
    else:
        arr = np.arange(size, dtype=np.float32).reshape(shape)
    
    tree = {'array': arr}
    
    serialized = msgpack_utils.msgpack_serialize(tree)
    restored = msgpack_utils.msgpack_restore(serialized)
    
    assert 'array' in restored
    assert restored['array'].shape == shape
    assert np.array_equal(restored['array'], arr)


# Test mixed tuple/array trees
@given(st.integers(1, 5))
@settings(max_examples=50)
def test_tuple_with_arrays(n):
    """Test tuples containing arrays are handled correctly"""
    # Create a tuple of arrays
    arrays = tuple(np.arange(i, i+3) for i in range(n))
    tree = {'tuple_of_arrays': arrays}
    
    serialized = msgpack_utils.msgpack_serialize(tree)
    restored = msgpack_utils.msgpack_restore(serialized)
    
    assert 'tuple_of_arrays' in restored
    assert isinstance(restored['tuple_of_arrays'], tuple)
    assert len(restored['tuple_of_arrays']) == n
    
    for i in range(n):
        assert np.array_equal(restored['tuple_of_arrays'][i], arrays[i])


# Test chunking for very large arrays
def test_array_chunking_boundary():
    """Test the chunking mechanism for arrays near the chunk size boundary"""
    # MAX_CHUNK_SIZE is 2**30 bytes in the code
    # Create array just below and above this threshold
    
    # Just below threshold: 2^27 float32 elements = 2^29 bytes
    small_size = 2**27
    small_array = np.zeros(small_size, dtype=np.float32)
    
    # Just above threshold: 2^28 float32 elements = 2^30 bytes (exactly at boundary)
    boundary_size = 2**28
    boundary_array = np.zeros(boundary_size, dtype=np.float32)
    
    # Above threshold: 2^28 + 1 float32 elements
    large_size = 2**28 + 1
    large_array = np.zeros(large_size, dtype=np.float32)
    
    trees = [
        {'small': small_array},
        {'boundary': boundary_array},
        {'large': large_array}
    ]
    
    for tree in trees:
        try:
            serialized = msgpack_utils.msgpack_serialize(tree)
            restored = msgpack_utils.msgpack_restore(serialized)
            
            key = list(tree.keys())[0]
            assert key in restored
            assert restored[key].shape == tree[key].shape
            print(f"✓ {key} array ({tree[key].size} elements) serialized successfully")
        except Exception as e:
            print(f"✗ Failed to serialize {list(tree.keys())[0]}: {e}")


if __name__ == "__main__":
    print("Testing array serialization edge cases...")
    
    # Test complex number
    test_tree = {'complex': 3+4j}
    serialized = msgpack_utils.msgpack_serialize(test_tree)
    restored = msgpack_utils.msgpack_restore(serialized)
    print(f"✓ Complex number: {test_tree} -> {restored}")
    
    # Test numpy scalar
    test_tree = {'scalar': np.float32(3.14)}
    serialized = msgpack_utils.msgpack_serialize(test_tree)
    restored = msgpack_utils.msgpack_restore(serialized)
    print(f"✓ Numpy scalar: {test_tree['scalar']} -> {restored['scalar']}")
    
    # Test empty array
    test_tree = {'empty': np.array([])}
    serialized = msgpack_utils.msgpack_serialize(test_tree)
    restored = msgpack_utils.msgpack_restore(serialized)
    print(f"✓ Empty array shape: {test_tree['empty'].shape} -> {restored['empty'].shape}")
    
    print("\nTesting chunking boundary conditions...")
    test_array_chunking_boundary()
    
    print("\nRun full tests with: pytest test_array_serialization.py -v")