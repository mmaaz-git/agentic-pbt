import numpy as np
import numpy.dtypes
from hypothesis import given, strategies as st, assume, settings, note
import math
import pytest


# Test for actual bugs in dtype handling

@given(st.sampled_from([numpy.dtypes.DateTime64DType, numpy.dtypes.TimeDelta64DType]))
def test_datetime_dtype_instantiation(dtype_class):
    """Test if DateTime64 and TimeDelta64 dtypes can be instantiated"""
    try:
        dt = dtype_class()
        print(f"Created {dtype_class.__name__}: {dt}")
        # Test if we can create arrays with it
        arr = np.array([1, 2, 3], dtype=dt)
        assert arr.dtype.kind in ['m', 'M']
    except Exception as e:
        print(f"Error with {dtype_class.__name__}: {e}")
        raise


@given(st.integers(1, 100))
def test_bytes_string_dtype_requires_size(size):
    """BytesDType and StrDType require size parameter"""
    # This should work
    bytes_dt = numpy.dtypes.BytesDType(size)
    str_dt = numpy.dtypes.StrDType(size)
    
    assert bytes_dt.itemsize == size
    assert str_dt.itemsize == size * 4  # Unicode uses 4 bytes per char
    
    # Test array creation
    arr_bytes = np.array([b'test'], dtype=bytes_dt)
    arr_str = np.array(['test'], dtype=str_dt)


@given(st.sampled_from([
    numpy.dtypes.Float16DType,
    numpy.dtypes.Float32DType,
    numpy.dtypes.Float64DType,
]))
def test_float_dtype_comparison_with_complex(float_dtype_class):
    """Test if float dtypes handle comparison with complex dtypes correctly"""
    float_dt = float_dtype_class()
    complex_dt = numpy.dtypes.Complex128DType()
    
    # These should be different types
    assert float_dt != complex_dt
    assert not (float_dt == complex_dt)
    
    # But can we convert between them?
    arr_float = np.array([1.5, 2.5], dtype=float_dt)
    arr_complex = arr_float.astype(complex_dt)
    assert arr_complex.dtype == complex_dt
    assert np.allclose(arr_complex.real, arr_float)
    assert np.allclose(arr_complex.imag, 0)


@given(
    st.sampled_from([
        numpy.dtypes.Int8DType,
        numpy.dtypes.Int16DType,
        numpy.dtypes.Int32DType,
        numpy.dtypes.Int64DType,
    ]),
    st.sampled_from([
        numpy.dtypes.UInt8DType,
        numpy.dtypes.UInt16DType,
        numpy.dtypes.UInt32DType,
        numpy.dtypes.UInt64DType,
    ])
)
def test_signed_unsigned_dtype_conversion(signed_dtype_class, unsigned_dtype_class):
    """Test conversion between signed and unsigned integer dtypes"""
    signed_dt = signed_dtype_class()
    unsigned_dt = unsigned_dtype_class()
    
    # Test with negative values
    arr_signed = np.array([-1, -2, -3], dtype=signed_dt)
    
    # Converting negative to unsigned should wrap around
    with np.errstate(over='ignore'):
        arr_unsigned = arr_signed.astype(unsigned_dt)
    
    # The values should wrap to large positive numbers
    assert np.all(arr_unsigned > 0)
    
    # Converting back should not recover original values (data loss)
    arr_back = arr_unsigned.astype(signed_dt)
    
    # Check if conversion is lossy when values are too large
    info_unsigned = np.iinfo(unsigned_dt)
    if info_unsigned.max > np.iinfo(signed_dt).max:
        # Large unsigned values don't fit in signed
        large_val = info_unsigned.max
        arr_large = np.array([large_val], dtype=unsigned_dt)
        arr_converted = arr_large.astype(signed_dt)
        # Should overflow to negative
        assert arr_converted[0] < 0


@given(st.sampled_from([
    numpy.dtypes.BoolDType,
    numpy.dtypes.Int8DType,
    numpy.dtypes.Float32DType,
]))
def test_dtype_newbyteorder_method(dtype_class):
    """Test if dtypes support newbyteorder method"""
    dt = dtype_class()
    
    # Test newbyteorder
    if hasattr(dt, 'newbyteorder'):
        dt_swapped = dt.newbyteorder()
        
        # Byteorder should change
        if dt.byteorder in ['<', '>']:
            expected = '>' if dt.byteorder == '<' else '<'
            assert dt_swapped.byteorder == expected
        
        # But the type should remain the same
        assert dt_swapped.kind == dt.kind
        assert dt_swapped.itemsize == dt.itemsize


@given(st.integers(1, 1000))
def test_void_dtype_creation(size):
    """Test VoidDType with different sizes"""
    dt = numpy.dtypes.VoidDType(size)
    assert dt.itemsize == size
    assert dt.kind == 'V'
    
    # Create array with void dtype
    arr = np.zeros(10, dtype=dt)
    assert arr.dtype == dt
    assert arr.itemsize == size


@given(st.sampled_from([
    (numpy.dtypes.Float32DType, numpy.dtypes.Float64DType),
    (numpy.dtypes.Int16DType, numpy.dtypes.Int32DType),
    (numpy.dtypes.Complex64DType, numpy.dtypes.Complex128DType),
]))
def test_dtype_precision_hierarchy(smaller_class, larger_class):
    """Test precision hierarchy between related dtypes"""
    smaller_dt = smaller_class()
    larger_dt = larger_class()
    
    # Larger dtype should have more itemsize
    assert larger_dt.itemsize > smaller_dt.itemsize
    
    # Test precision preservation in conversion
    if 'int' in smaller_dt.name:
        # For integers, all values in smaller range should convert exactly
        info_small = np.iinfo(smaller_dt)
        test_vals = [info_small.min, info_small.max]
        arr_small = np.array(test_vals, dtype=smaller_dt)
        arr_large = arr_small.astype(larger_dt)
        arr_back = arr_large.astype(smaller_dt)
        assert np.array_equal(arr_small, arr_back)


@given(st.sampled_from([
    numpy.dtypes.Float16DType,
    numpy.dtypes.Float32DType,
    numpy.dtypes.Float64DType,
]))
def test_float_dtype_subnormal_handling(dtype_class):
    """Test handling of subnormal (denormalized) numbers"""
    dt = dtype_class()
    info = np.finfo(dt)
    
    # Test smallest normal and subnormal values
    smallest_normal = info.tiny
    
    # Create array with very small values
    arr = np.array([smallest_normal, smallest_normal/2, smallest_normal/10], dtype=dt)
    
    # These should not become zero (unless below min subnormal)
    if dt == numpy.dtypes.Float64DType:
        # Float64 has extensive subnormal range
        assert arr[1] != 0  # smallest_normal/2 should be subnormal, not zero
    
    # But dividing by huge number should eventually give zero
    arr_zero = np.array([smallest_normal / (2**100)], dtype=dt)
    assert arr_zero[0] == 0


@given(st.sampled_from([
    numpy.dtypes.Int8DType,
    numpy.dtypes.Int16DType,
    numpy.dtypes.Int32DType,
    numpy.dtypes.Int64DType,
]))
def test_integer_dtype_type_property(dtype_class):
    """Test the 'type' property of integer dtypes"""
    dt = dtype_class()
    
    # dtype should have a 'type' attribute pointing to scalar type
    assert hasattr(dt, 'type')
    
    # Create a scalar with this type
    scalar = dt.type(42)
    assert isinstance(scalar, np.generic)
    assert scalar == 42
    
    # The scalar's dtype should match
    assert scalar.dtype == dt


# Test for potential edge cases and bugs

@given(st.sampled_from([numpy.dtypes.Complex64DType, numpy.dtypes.Complex128DType]))
def test_complex_dtype_real_imag_dtypes(complex_dtype_class):
    """Test if complex dtypes correctly report their component dtypes"""
    dt = complex_dtype_class()
    
    # Complex dtypes should specify their real/imag component types
    arr = np.array([1+2j, 3+4j], dtype=dt)
    
    real_dtype = arr.real.dtype
    imag_dtype = arr.imag.dtype
    
    # Real and imag parts should have matching float precision
    assert real_dtype == imag_dtype
    
    if dt == numpy.dtypes.Complex64DType:
        assert real_dtype == np.float32
    elif dt == numpy.dtypes.Complex128DType:
        assert real_dtype == np.float64


@given(st.integers(0, 255))
def test_uint8_dtype_wraparound(value):
    """Test uint8 wraparound behavior"""
    dt = numpy.dtypes.UInt8DType()
    
    # Adding 256 should wrap around
    arr = np.array([value], dtype=dt)
    result = arr + np.array([256], dtype=dt)
    
    # 256 wraps to 0 in uint8, so result should equal original
    assert result[0] == value
    
    # Subtracting from 0 should wrap to 255
    if value == 0:
        result = arr - np.array([1], dtype=dt)
        assert result[0] == 255


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])