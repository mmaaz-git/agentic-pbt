import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from spnego.iov import BufferType, IOVBuffer, IOVResBuffer
import typing


# Bug hunting test 1: Can BufferType handle negative values consistently?
@given(st.integers(min_value=-2**31, max_value=-1))
def test_buffertype_negative_values(value):
    """BufferType should consistently handle negative values."""
    # All negative values should raise ValueError
    with pytest.raises(ValueError):
        BufferType(value)


# Bug hunting test 2: BufferType arithmetic operations
@given(st.sampled_from(list(BufferType)))
def test_buffertype_arithmetic_preserves_type(buffer_type):
    """BufferType arithmetic should preserve IntEnum behavior."""
    # IntEnum should support arithmetic but return int
    result = buffer_type + 1
    assert isinstance(result, int)
    assert result == buffer_type.value + 1
    
    # Subtracting
    result = buffer_type - 1
    assert isinstance(result, int)
    assert result == buffer_type.value - 1
    
    # Multiplication
    result = buffer_type * 2
    assert isinstance(result, int)
    assert result == buffer_type.value * 2


# Bug hunting test 3: IOVBuffer with very large integers
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    huge_int=st.integers(min_value=2**63-100, max_value=2**63+100)
)
def test_iovbuffer_with_huge_integers(buffer_type, huge_int):
    """IOVBuffer should handle very large integers."""
    assume(huge_int >= 0)  # Only positive values make sense for buffer sizes
    buffer = IOVBuffer(type=buffer_type, data=huge_int)
    assert buffer.type == buffer_type
    assert buffer.data == huge_int


# Bug hunting test 4: IOVBuffer with mixed types in sequence
@given(
    data_list=st.lists(
        st.one_of(
            st.binary(max_size=10),
            st.integers(min_value=0, max_value=100),
            st.booleans(),
            st.none()
        ),
        min_size=2,
        max_size=5
    )
)
def test_iovbuffer_sequence_with_mixed_types(data_list):
    """Creating multiple IOVBuffers with mixed data types."""
    buffers = []
    for data in data_list:
        buffer = IOVBuffer(type=BufferType.data, data=data)
        buffers.append(buffer)
    
    # Verify all buffers were created correctly
    for i, buffer in enumerate(buffers):
        assert buffer.type == BufferType.data
        assert buffer.data == data_list[i]


# Bug hunting test 5: IOVBuffer comparison edge cases
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    data1=st.one_of(st.integers(min_value=0, max_value=10), st.booleans()),
    data2=st.one_of(st.integers(min_value=0, max_value=10), st.booleans())
)
def test_iovbuffer_comparison_with_coercible_types(buffer_type, data1, data2):
    """IOVBuffer comparison with potentially coercible types."""
    buffer1 = IOVBuffer(type=buffer_type, data=data1)
    buffer2 = IOVBuffer(type=buffer_type, data=data2)
    
    # Buffers should only be equal if data is exactly equal
    if data1 == data2:
        assert buffer1 == buffer2
    else:
        assert buffer1 != buffer2
    
    # Special case: True == 1 and False == 0 in Python
    if isinstance(data1, bool) and isinstance(data2, int):
        if (data1 is True and data2 == 1) or (data1 is False and data2 == 0):
            # Python considers these equal
            assert data1 == data2
            assert buffer1 == buffer2
    elif isinstance(data2, bool) and isinstance(data1, int):
        if (data2 is True and data1 == 1) or (data2 is False and data1 == 0):
            # Python considers these equal
            assert data1 == data2
            assert buffer1 == buffer2


# Bug hunting test 6: BufferType with float-like values
@given(st.floats(min_value=0, max_value=5000, allow_nan=False, allow_infinity=False))
def test_buffertype_with_float_values(value):
    """BufferType accepts floats that are exactly equal to integers."""
    int_value = int(value)
    valid_values = {0, 1, 2, 3, 7, 9, 10, 11, 12, 4096}
    
    if int_value in valid_values:
        # Should accept integer conversion
        bt = BufferType(int_value)
        assert bt.value == int_value
        
        # IntEnum accepts floats that are exactly equal to integers
        if value == int_value:  # e.g., 1.0, 2.0
            bt_float = BufferType(value)
            assert bt_float == bt
        else:  # e.g., 1.5, 2.3
            with pytest.raises(ValueError):
                BufferType(value)
    else:
        with pytest.raises(ValueError):
            BufferType(int_value)


# Bug hunting test 7: IOVBuffer field access patterns
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    data=st.binary(max_size=100)
)
def test_iovbuffer_attribute_vs_index_access(buffer_type, data):
    """IOVBuffer attribute and index access should be consistent."""
    buffer = IOVBuffer(type=buffer_type, data=data)
    
    # Named access
    assert buffer.type == buffer_type
    assert buffer.data == data
    
    # Index access
    assert buffer[0] == buffer_type
    assert buffer[1] == data
    
    # Both should refer to same object
    assert buffer.type is buffer[0]
    assert buffer.data is buffer[1]


# Bug hunting test 8: BufferType boolean operations
@given(st.sampled_from(list(BufferType)))
def test_buffertype_boolean_evaluation(buffer_type):
    """BufferType boolean evaluation should follow int rules."""
    # BufferType inherits from int, so it should follow int's truthiness
    if buffer_type.value == 0:
        assert not bool(buffer_type)
        assert not buffer_type  # Direct boolean context
    else:
        assert bool(buffer_type)
        assert buffer_type  # Direct boolean context


# Bug hunting test 9: IOVBuffer with special byte sequences
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    special_bytes=st.one_of(
        st.just(b'\x00' * 100),  # Null bytes
        st.just(b'\xff' * 100),  # Max bytes
        st.just(b'\x00\xff' * 50),  # Alternating
        st.just(b''),  # Empty
    )
)
def test_iovbuffer_with_special_bytes(buffer_type, special_bytes):
    """IOVBuffer should handle special byte sequences."""
    buffer = IOVBuffer(type=buffer_type, data=special_bytes)
    assert buffer.type == buffer_type
    assert buffer.data == special_bytes
    
    # Ensure it's the exact same bytes object
    assert buffer.data is special_bytes or buffer.data == special_bytes


# Bug hunting test 10: Type confusion between int and BufferType
@given(
    int_value=st.sampled_from([0, 1, 2, 3, 7, 9, 10, 11, 12, 4096]),
    data=st.binary(max_size=10)
)
def test_iovbuffer_type_confusion(int_value, data):
    """IOVBuffer should handle both int and BufferType for type field."""
    # Create with int
    buffer1 = IOVBuffer(type=int_value, data=data)
    
    # Create with BufferType
    buffer2 = IOVBuffer(type=BufferType(int_value), data=data)
    
    # They should be equal
    assert buffer1 == buffer2
    
    # But the type field might be different types
    assert buffer1.type == buffer2.type  # Values are equal
    # Note: buffer1.type might be int while buffer2.type is BufferType


# Bug hunting test 11: IOVResBuffer type validation at runtime
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    invalid_data=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers(), min_size=1, max_size=3)
    )
)
def test_iovresbuffer_accepts_invalid_types(buffer_type, invalid_data):
    """IOVResBuffer doesn't validate types at runtime (NamedTuple limitation)."""
    # This is a potential issue: IOVResBuffer accepts invalid data types
    # even though its type annotation says Optional[bytes]
    buffer = IOVResBuffer(type=buffer_type, data=invalid_data)
    assert buffer.type == buffer_type
    assert buffer.data == invalid_data
    # This violates the type contract but Python doesn't enforce it at runtime


# Bug hunting test 12: BufferType with string integers
@given(st.sampled_from(['0', '1', '2', '3', '7', '9', '10', '11', '12', '4096']))
def test_buffertype_string_integer_conversion(str_value):
    """BufferType should handle string integer conversion."""
    int_value = int(str_value)
    
    # Should work with integer
    bt1 = BufferType(int_value)
    assert bt1.value == int_value
    
    # Should not work with string directly
    with pytest.raises((ValueError, TypeError)):
        BufferType(str_value)