"""Run property-based tests for awkward.typetracer module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import traceback
import numpy as np
from hypothesis import given, strategies as st, assume, settings, Verbosity
import awkward.typetracer as tt
import awkward as ak

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

print("Running property-based tests for awkward.typetracer...")
print("=" * 60)

test_results = []

# Test 1: create_unknown_scalar dtype preservation
print("\nTest 1: create_unknown_scalar dtype preservation")
@given(dtype=valid_dtypes)
@settings(max_examples=100, verbosity=Verbosity.normal)
def test_create_unknown_scalar_dtype_preservation(dtype):
    scalar = tt.create_unknown_scalar(dtype)
    assert scalar.dtype == dtype
    assert scalar.ndim == 0
    assert scalar.shape == ()

try:
    test_create_unknown_scalar_dtype_preservation()
    print("✓ PASSED")
    test_results.append(("test_create_unknown_scalar_dtype_preservation", "PASSED"))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("test_create_unknown_scalar_dtype_preservation", f"FAILED: {e}"))
    traceback.print_exc()

# Test 2: TypeTracerArray shape/dtype preservation
print("\nTest 2: TypeTracerArray shape/dtype preservation")
@given(dtype=valid_dtypes, shape=shapes)
@settings(max_examples=100, verbosity=Verbosity.normal)
def test_typetracer_array_shape_dtype_preservation(dtype, shape):
    array = tt.TypeTracerArray._new(dtype, shape)
    assert array.dtype == dtype
    assert array.shape == shape
    assert array.ndim == len(shape)

try:
    test_typetracer_array_shape_dtype_preservation()
    print("✓ PASSED")
    test_results.append(("test_typetracer_array_shape_dtype_preservation", "PASSED"))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("test_typetracer_array_shape_dtype_preservation", f"FAILED: {e}"))
    traceback.print_exc()

# Test 3: view() divisibility invariant
print("\nTest 3: TypeTracerArray.view() divisibility invariant")
@given(
    dtype=valid_dtypes,
    shape=st.lists(small_ints, min_size=1, max_size=4).map(tuple)
)
@settings(max_examples=100, verbosity=Verbosity.normal)
def test_typetracer_array_view_divisibility(dtype, shape):
    array = tt.TypeTracerArray._new(dtype, shape)
    
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
            original_bytes = array.nbytes
            viewed_bytes = viewed.nbytes
            
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

try:
    test_typetracer_array_view_divisibility()
    print("✓ PASSED")
    test_results.append(("test_typetracer_array_view_divisibility", "PASSED"))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("test_typetracer_array_view_divisibility", f"FAILED: {e}"))
    traceback.print_exc()

# Test 4: Transpose property
print("\nTest 4: TypeTracerArray transpose (T) property")
@given(
    dtype=valid_dtypes,
    shape=st.lists(small_ints, min_size=1, max_size=3).map(tuple)
)
@settings(max_examples=100, verbosity=Verbosity.normal)
def test_typetracer_array_transpose_property(dtype, shape):
    array = tt.TypeTracerArray._new(dtype, shape)
    transposed = array.T
    
    assert transposed.dtype == dtype
    assert transposed.shape == shape[::-1]
    assert transposed.ndim == len(shape)
    
    # Double transpose should give original shape
    double_transposed = transposed.T
    assert double_transposed.shape == shape

try:
    test_typetracer_array_transpose_property()
    print("✓ PASSED")
    test_results.append(("test_typetracer_array_transpose_property", "PASSED"))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("test_typetracer_array_transpose_property", f"FAILED: {e}"))
    traceback.print_exc()

# Test 5: Unknown scalar detection
print("\nTest 5: is_unknown_scalar detection")
@given(dtype=valid_dtypes)
@settings(max_examples=100, verbosity=Verbosity.normal)
def test_is_unknown_scalar_detection(dtype):
    scalar = tt.create_unknown_scalar(dtype)
    assert tt.is_unknown_scalar(scalar) is True
    assert tt.is_unknown_array(scalar) is False
    
    # Non-scalar should not be detected as scalar
    array = tt.TypeTracerArray._new(dtype, (5, 3))
    assert tt.is_unknown_scalar(array) is False
    assert tt.is_unknown_array(array) is True

try:
    test_is_unknown_scalar_detection()
    print("✓ PASSED")
    test_results.append(("test_is_unknown_scalar_detection", "PASSED"))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("test_is_unknown_scalar_detection", f"FAILED: {e}"))
    traceback.print_exc()

# Test 6: Size calculation
print("\nTest 6: TypeTracerArray size calculation")
@given(
    dtype=valid_dtypes,
    shape=st.lists(small_ints, min_size=1, max_size=3).map(tuple)
)
@settings(max_examples=100, verbosity=Verbosity.normal)
def test_typetracer_array_size_calculation(dtype, shape):
    array = tt.TypeTracerArray._new(dtype, shape)
    
    expected_size = 1
    for dim in shape:
        expected_size *= dim
    
    assert array.size == expected_size
    assert array.nbytes == expected_size * dtype.itemsize

try:
    test_typetracer_array_size_calculation()
    print("✓ PASSED")
    test_results.append(("test_typetracer_array_size_calculation", "PASSED"))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("test_typetracer_array_size_calculation", f"FAILED: {e}"))
    traceback.print_exc()

# Test 7: forget_length
print("\nTest 7: TypeTracerArray forget_length")
@given(
    dtype=valid_dtypes,
    shape=st.lists(small_ints, min_size=1, max_size=3).map(tuple)
)
@settings(max_examples=100, verbosity=Verbosity.normal)
def test_forget_length_sets_unknown(dtype, shape):
    array = tt.TypeTracerArray._new(dtype, shape)
    forgotten = array.forget_length()
    
    assert forgotten.dtype == dtype
    assert forgotten.shape[0] is tt.unknown_length
    assert forgotten.shape[1:] == shape[1:]

try:
    test_forget_length_sets_unknown()
    print("✓ PASSED")
    test_results.append(("test_forget_length_sets_unknown", "PASSED"))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("test_forget_length_sets_unknown", f"FAILED: {e}"))
    traceback.print_exc()

# Test 8: MaybeNone equality
print("\nTest 8: MaybeNone equality")
@given(shape=shapes)
@settings(max_examples=50, verbosity=Verbosity.normal)
def test_maybe_none_equality(shape):
    content1 = tt.TypeTracerArray._new(np.dtype('float64'), shape)
    content2 = tt.TypeTracerArray._new(np.dtype('float64'), shape)
    
    maybe1 = tt.MaybeNone(content1)
    maybe2 = tt.MaybeNone(content1)  # Same content
    
    assert maybe1 == maybe2

try:
    test_maybe_none_equality()
    print("✓ PASSED")
    test_results.append(("test_maybe_none_equality", "PASSED"))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("test_maybe_none_equality", f"FAILED: {e}"))
    traceback.print_exc()

# Print summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)

passed = sum(1 for _, result in test_results if result == "PASSED")
failed = len(test_results) - passed

for test_name, result in test_results:
    status = "✓" if result == "PASSED" else "✗"
    print(f"{status} {test_name}: {result}")

print(f"\nTotal: {passed} passed, {failed} failed out of {len(test_results)} tests")

if failed == 0:
    print("\n✅ All tests passed!")
else:
    print(f"\n❌ {failed} test(s) failed")
    sys.exit(1)