"""Property-based tests for awkward.typetracer module using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
from hypothesis import given, strategies as st, assume, settings
import awkward.typetracer as tt
import awkward as ak
import pytest

# Strategy for valid numpy dtypes
valid_dtypes = st.sampled_from([
    np.dtype('int8'), np.dtype('int16'), np.dtype('int32'), np.dtype('int64'),
    np.dtype('uint8'), np.dtype('uint16'), np.dtype('uint32'), np.dtype('uint64'),
    np.dtype('float32'), np.dtype('float64'),
    np.dtype('bool'), np.dtype('complex64'), np.dtype('complex128')
])

# Strategy for small positive integers (for shape dimensions)
small_ints = st.integers(min_value=1, max_value=100)

# Strategy for shapes (tuples of small positive integers)
shapes = st.lists(small_ints, min_size=0, max_size=4).map(tuple)


@given(dtype=valid_dtypes)
def test_create_unknown_scalar_dtype_preservation(dtype):
    """Test that create_unknown_scalar preserves the dtype correctly."""
    scalar = tt.create_unknown_scalar(dtype)
    assert scalar.dtype == dtype
    assert scalar.ndim == 0
    assert scalar.shape == ()


@given(dtype=valid_dtypes, shape=shapes)
def test_typetracer_array_shape_dtype_preservation(dtype, shape):
    """Test that TypeTracerArray preserves shape and dtype."""
    array = tt.TypeTracerArray._new(dtype, shape)
    assert array.dtype == dtype
    assert array.shape == shape
    assert array.ndim == len(shape)


@given(
    dtype=valid_dtypes,
    shape=st.lists(small_ints, min_size=1, max_size=4).map(tuple)
)
def test_typetracer_array_view_divisibility(dtype, shape):
    """Test the view() method's divisibility invariant."""
    array = tt.TypeTracerArray._new(dtype, shape)
    
    # Try to view with a dtype of different size
    target_dtypes = [
        np.dtype('int8'), np.dtype('int16'), np.dtype('int32'), np.dtype('int64'),
        np.dtype('float32'), np.dtype('float64')
    ]
    
    for target_dtype in target_dtypes:
        if target_dtype == dtype:
            continue
            
        try:
            viewed = array.view(target_dtype)
            
            # If view succeeded, check the invariant
            # The total bytes should be preserved
            original_bytes = array.nbytes
            viewed_bytes = viewed.nbytes
            
            # For unknown lengths, we can't verify byte preservation
            if original_bytes != tt.unknown_length and viewed_bytes != tt.unknown_length:
                assert original_bytes == viewed_bytes, f"View changed total bytes: {original_bytes} != {viewed_bytes}"
                
            # Check that the last dimension was adjusted correctly
            if len(shape) > 0:
                last_dim_bytes = shape[-1] * dtype.itemsize
                new_last_dim = last_dim_bytes // target_dtype.itemsize
                if last_dim_bytes % target_dtype.itemsize == 0:
                    assert viewed.shape[-1] == new_last_dim
                    
        except ValueError as e:
            # View should fail if the sizes don't divide evenly
            if len(shape) > 0:
                last_dim_bytes = shape[-1] * dtype.itemsize
                remainder = last_dim_bytes % target_dtype.itemsize
                assert remainder != 0, f"View raised ValueError but should have succeeded: {e}"


@given(
    dtype=valid_dtypes,
    shape=st.lists(small_ints, min_size=1, max_size=3).map(tuple)
)
def test_typetracer_array_transpose_property(dtype, shape):
    """Test that transpose (T property) reverses shape correctly."""
    array = tt.TypeTracerArray._new(dtype, shape)
    transposed = array.T
    
    assert transposed.dtype == dtype
    assert transposed.shape == shape[::-1]
    assert transposed.ndim == len(shape)
    
    # Double transpose should give original shape
    double_transposed = transposed.T
    assert double_transposed.shape == shape


@given(dtype=valid_dtypes)
def test_is_unknown_scalar_detection(dtype):
    """Test that is_unknown_scalar correctly identifies scalar TypeTracerArrays."""
    scalar = tt.create_unknown_scalar(dtype)
    assert tt.is_unknown_scalar(scalar) is True
    assert tt.is_unknown_array(scalar) is False
    
    # Non-scalar should not be detected as scalar
    array = tt.TypeTracerArray._new(dtype, (5, 3))
    assert tt.is_unknown_scalar(array) is False
    assert tt.is_unknown_array(array) is True


@given(
    dtype=valid_dtypes,
    shape=st.lists(small_ints, min_size=1, max_size=3).map(tuple)
)
def test_typetracer_array_size_calculation(dtype, shape):
    """Test that size property correctly calculates total number of elements."""
    array = tt.TypeTracerArray._new(dtype, shape)
    
    expected_size = 1
    for dim in shape:
        expected_size *= dim
    
    assert array.size == expected_size
    
    # nbytes should be size * itemsize
    assert array.nbytes == expected_size * dtype.itemsize


@given(
    dtype=valid_dtypes,
    shape=st.lists(small_ints, min_size=2, max_size=4).map(tuple)
)
def test_typetracer_array_inner_shape(dtype, shape):
    """Test that inner_shape returns all dimensions except the first."""
    array = tt.TypeTracerArray._new(dtype, shape)
    assert array.inner_shape == shape[1:]


@given(
    shape=st.lists(small_ints, min_size=1, max_size=3).map(tuple)
)
def test_typetracer_report_tracking(shape):
    """Test that TypeTracerReport correctly tracks shape and data touches."""
    report = tt.TypeTracerReport()
    form_key = "test_key"
    
    # Set up labels
    report.set_labels([form_key])
    
    # Create a TypeTracerArray with report
    array = tt.TypeTracerArray._new(np.dtype('float64'), shape, form_key=form_key, report=report)
    
    # Touch shape
    _ = array.shape
    assert form_key in report.shape_touched
    
    # Touch data
    array.touch_data()
    assert form_key in report.data_touched
    # Touching data should also touch shape
    assert form_key in report.shape_touched


@given(
    dtype=valid_dtypes,
    shape=st.lists(small_ints, min_size=1, max_size=3).map(tuple)
)  
def test_forget_length_sets_unknown(dtype, shape):
    """Test that forget_length() sets the first dimension to unknown_length."""
    array = tt.TypeTracerArray._new(dtype, shape)
    forgotten = array.forget_length()
    
    assert forgotten.dtype == dtype
    assert forgotten.shape[0] is tt.unknown_length
    assert forgotten.shape[1:] == shape[1:]


@given(
    dtype=valid_dtypes,
    outer_shape=st.lists(small_ints, min_size=1, max_size=2).map(tuple),
    inner_shape=st.lists(small_ints, min_size=0, max_size=2).map(tuple)
)
def test_typetracer_array_getitem_slice_preserves_structure(dtype, outer_shape, inner_shape):
    """Test that slicing operations preserve array structure correctly."""
    full_shape = outer_shape + inner_shape
    array = tt.TypeTracerArray._new(dtype, full_shape)
    
    # Test simple slice
    if len(full_shape) > 0:
        sliced = array[:]
        assert sliced.dtype == dtype
        assert sliced.shape == full_shape
        
        # Test slice with step
        sliced_step = array[::2]
        assert sliced_step.dtype == dtype
        if len(full_shape) > 0:
            # First dimension should be halved (approximately)
            expected_first_dim = (full_shape[0] + 1) // 2
            assert sliced_step.shape[0] == expected_first_dim
            assert sliced_step.shape[1:] == full_shape[1:]


@given(shape=shapes)
def test_maybe_none_equality(shape):
    """Test MaybeNone wrapper equality."""
    content1 = tt.TypeTracerArray._new(np.dtype('float64'), shape)
    content2 = tt.TypeTracerArray._new(np.dtype('float64'), shape)
    
    maybe1 = tt.MaybeNone(content1)
    maybe2 = tt.MaybeNone(content1)  # Same content
    maybe3 = tt.MaybeNone(content2)  # Different content object
    
    assert maybe1 == maybe2
    # Note: TypeTracerArray doesn't define __eq__, so maybe1 != maybe3


@given(
    dtypes=st.lists(valid_dtypes, min_size=2, max_size=4),
    shape=shapes
)
def test_one_of_equality(dtypes, shape):
    """Test OneOf wrapper equality with set semantics."""
    contents = [tt.TypeTracerArray._new(dt, shape) for dt in dtypes]
    
    oneof1 = tt.OneOf(contents)
    oneof2 = tt.OneOf(contents[::-1])  # Reversed order
    oneof3 = tt.OneOf(contents[:-1])  # Missing one element
    
    # OneOf uses set equality, so order doesn't matter
    assert oneof1 == oneof2
    if len(contents) > 1:
        assert oneof1 != oneof3


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])