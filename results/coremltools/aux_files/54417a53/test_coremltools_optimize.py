"""Property-based tests for coremltools.optimize module"""

import math
import numpy as np
import pytest
from hypothesis import given, strategies as st, assume, settings
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

from coremltools.optimize._utils import (
    quantize_by_scale_and_zp,
    dequantize_by_scale_and_zp,
    pack_elements_into_bits,
    restore_elements_from_packed_bits,
    get_quant_range,
    lut_to_dense,
    sparse_to_dense,
    find_indices_for_lut,
    repeat_data_as
)
from coremltools.converters.mil.mil import types


# Strategy for reasonable floating point arrays
reasonable_floats = st.floats(
    min_value=-1e10, 
    max_value=1e10, 
    allow_nan=False, 
    allow_infinity=False,
    width=32
)

# Strategy for small arrays to avoid memory issues
small_array_strategy = st.lists(
    reasonable_floats,
    min_size=1,
    max_size=100
).map(lambda x: np.array(x, dtype=np.float32))


@given(
    data=small_array_strategy,
    nbits=st.sampled_from([4, 8]),  # Common quantization bit widths
    signed=st.booleans()
)
@settings(max_examples=100)
def test_quantize_dequantize_round_trip(data, nbits, signed):
    """Test that quantization followed by dequantization preserves data approximately"""
    # Get the appropriate dtype string
    dtype_str = f"{'int' if signed else 'uint'}{nbits}"
    output_dtype = types.string_to_builtin(dtype_str)
    
    # Create a reasonable scale (avoid too small to prevent numerical issues)
    data_range = np.max(data) - np.min(data)
    if data_range < 1e-10:
        data_range = 1.0
    scale = np.array([data_range / (2**nbits - 1)], dtype=np.float32)
    
    # Use zero_point for unsigned quantization
    zero_point = None
    if not signed:
        zero_point = np.array([2**(nbits-1)], dtype=types.nptype_from_builtin(output_dtype))
    
    # Quantize
    quantized = quantize_by_scale_and_zp(data, scale, zero_point, output_dtype)
    
    # Dequantize
    dequantized = dequantize_by_scale_and_zp(quantized, scale, zero_point)
    
    # Check that the round-trip preserves data approximately
    # The error should be bounded by the quantization step size
    max_error = scale[0] * 2  # Allow for some rounding error
    assert np.allclose(data, dequantized, atol=max_error, rtol=0.1)


@given(
    elements=st.lists(
        st.integers(min_value=0, max_value=15),  # 4-bit values
        min_size=1,
        max_size=100
    ),
    nbits=st.sampled_from([2, 4, 8])
)
def test_pack_unpack_bits_round_trip_unsigned(elements, nbits):
    """Test that packing and unpacking bits preserves unsigned integer data"""
    # Ensure elements fit in nbits
    max_val = 2**nbits - 1
    elements_array = np.array([min(e, max_val) for e in elements], dtype=np.uint8)
    
    # Pack the elements
    packed = pack_elements_into_bits(elements_array, nbits)
    
    # Unpack the elements
    unpacked = restore_elements_from_packed_bits(
        packed, nbits, len(elements_array), are_packed_values_signed=False
    )
    
    # Check round-trip property
    assert np.array_equal(elements_array, unpacked)


@given(
    elements=st.lists(
        st.integers(min_value=-8, max_value=7),  # 4-bit signed values
        min_size=1,
        max_size=100
    ),
    nbits=st.sampled_from([4, 8])
)
def test_pack_unpack_bits_round_trip_signed(elements, nbits):
    """Test that packing and unpacking bits preserves signed integer data"""
    # Ensure elements fit in nbits (signed)
    max_val = 2**(nbits-1) - 1
    min_val = -2**(nbits-1)
    elements_array = np.array(
        [max(min_val, min(e, max_val)) for e in elements], 
        dtype=np.int8
    )
    
    # Pack the elements
    packed = pack_elements_into_bits(elements_array, nbits)
    
    # Unpack the elements
    unpacked = restore_elements_from_packed_bits(
        packed, nbits, len(elements_array), are_packed_values_signed=True
    )
    
    # Check round-trip property
    assert np.array_equal(elements_array, unpacked)


@given(
    nbits=st.integers(min_value=1, max_value=16),
    signed=st.booleans()
)
def test_quant_range_validity(nbits, signed):
    """Test that quantization ranges are valid and consistent"""
    # Test both quantization modes
    for mode in ["LINEAR", "LINEAR_SYMMETRIC"]:
        min_val, max_val = get_quant_range(nbits, signed, mode)
        
        # Basic range checks
        assert min_val < max_val
        assert isinstance(min_val, int)
        assert isinstance(max_val, int)
        
        # Check range spans expected number of values
        if mode == "LINEAR":
            if signed:
                assert max_val - min_val == 2**nbits - 1
            else:
                assert max_val - min_val == 2**nbits - 1
        else:  # LINEAR_SYMMETRIC
            if signed:
                # Symmetric mode excludes one value for symmetry
                assert max_val - min_val == 2**nbits - 2
            else:
                # For unsigned symmetric, we exclude one value
                assert max_val - min_val == 2**nbits - 2


@given(
    shape=st.tuples(
        st.integers(min_value=1, max_value=10),
        st.integers(min_value=1, max_value=10)
    ),
    sparsity=st.floats(min_value=0.1, max_value=0.9)
)
def test_sparse_to_dense_reconstruction(shape, sparsity):
    """Test sparse to dense conversion preserves data"""
    # Create a random array
    original = np.random.randn(*shape).astype(np.float32)
    
    # Create a mask (1 where we keep values, 0 where we zero them out)
    mask = (np.random.random(shape) > sparsity).astype(np.uint8)
    
    # Create sparse representation
    nonzero_data = original[mask != 0]
    
    # Convert back to dense
    reconstructed = sparse_to_dense(nonzero_data, mask)
    
    # Check that non-zero positions match
    assert np.array_equal(reconstructed[mask != 0], nonzero_data)
    # Check that zero positions are zero
    assert np.all(reconstructed[mask == 0] == 0)


@given(
    data_shape=st.tuples(
        st.integers(min_value=2, max_value=8),
        st.integers(min_value=2, max_value=8)
    ),
    nbits=st.sampled_from([2, 3, 4])  # Small palette sizes for testing
)
@settings(max_examples=50)
def test_lut_find_indices_round_trip(data_shape, nbits):
    """Test that finding indices for LUT and then decompressing gives back similar data"""
    # Create random data
    data = np.random.randn(*data_shape).astype(np.float32)
    
    # Create a random LUT (palette)
    num_palettes = 2**nbits
    lut_shape = (1, 1, num_palettes, 1)  # Per-tensor LUT, scalar palettization
    lut = np.sort(np.random.randn(num_palettes))  # Sort for better coverage
    lut = lut.reshape(lut_shape).astype(np.float32)
    
    # Find best indices for the data
    indices = find_indices_for_lut(data, lut, vector_axis=None)
    
    # Decompress using the indices
    decompressed = lut_to_dense(indices, lut, vector_axis=None)
    
    # The decompressed values should be from the LUT
    unique_decompressed = np.unique(decompressed)
    lut_values = np.squeeze(lut)
    
    # Every decompressed value should be in the LUT
    for val in unique_decompressed:
        assert np.any(np.isclose(lut_values, val, atol=1e-6))


@given(
    input_shape=st.tuples(
        st.integers(min_value=2, max_value=10),
        st.integers(min_value=2, max_value=10)
    ),
    target_shape=st.tuples(
        st.integers(min_value=4, max_value=20),
        st.integers(min_value=4, max_value=20)
    )
)
def test_repeat_data_as_dimension_check(input_shape, target_shape):
    """Test that repeat_data_as correctly handles dimension constraints"""
    # Make target shape divisible by input shape
    target_shape = tuple(
        (t // i) * i for i, t in zip(input_shape, target_shape)
    )
    
    # Skip if any dimension becomes 0
    if any(t == 0 for t in target_shape):
        return
    
    # Create input data
    input_data = np.random.randn(*input_shape, 3).astype(np.float32)  # Extra dimension
    
    # Repeat the data
    repeated = repeat_data_as(input_data, target_shape)
    
    # Check shape
    assert repeated.shape[:2] == target_shape
    assert repeated.shape[2] == 3  # Extra dimension preserved
    
    # Check that data is repeated correctly
    block_sizes = tuple(t // i for i, t in zip(input_shape, target_shape))
    
    # Sample check: first block should match the pattern
    for i in range(block_sizes[0]):
        for j in range(block_sizes[1]):
            expected = input_data[0, 0]
            actual = repeated[i, j]
            assert np.array_equal(actual, expected)