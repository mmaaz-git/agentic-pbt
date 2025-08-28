import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from spnego.iov import BufferType, IOVBuffer, IOVResBuffer
import typing


# Advanced test 1: BufferType enum edge cases
@given(st.integers())
def test_buffertype_invalid_values_raise_valueerror(value):
    """Invalid BufferType values should raise ValueError."""
    valid_values = {bt.value for bt in BufferType}
    if value not in valid_values:
        with pytest.raises(ValueError):
            BufferType(value)
    else:
        # Valid values should work
        bt = BufferType(value)
        assert bt.value == value


# Advanced test 2: BufferType has expected values based on comments
def test_buffertype_expected_values():
    """BufferType should have specific values as documented."""
    assert BufferType.empty.value == 0
    assert BufferType.data.value == 1
    assert BufferType.header.value == 2
    assert BufferType.pkg_params.value == 3
    assert BufferType.trailer.value == 7
    assert BufferType.padding.value == 9
    assert BufferType.stream.value == 10
    assert BufferType.sign_only.value == 11
    assert BufferType.mic_token.value == 12
    assert BufferType.data_readonly.value == 4096


# Advanced test 3: Test NamedTuple behavior
@given(
    bt1=st.sampled_from(list(BufferType)),
    data1=st.one_of(st.none(), st.binary(max_size=100)),
    bt2=st.sampled_from(list(BufferType)),
    data2=st.one_of(st.none(), st.binary(max_size=100))
)
def test_iovbuffer_equality_and_hashing(bt1, data1, bt2, data2):
    """IOVBuffer equality and hashing should work correctly."""
    buffer1 = IOVBuffer(type=bt1, data=data1)
    buffer2 = IOVBuffer(type=bt2, data=data2)
    
    if bt1 == bt2 and data1 == data2:
        assert buffer1 == buffer2
        assert hash(buffer1) == hash(buffer2)
    else:
        assert buffer1 != buffer2
        # Note: different objects might have same hash (collision)
        # so we don't test hash inequality


# Advanced test 4: IOVBuffer can be unpacked
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    data=st.one_of(
        st.none(),
        st.binary(max_size=100),
        st.integers(min_value=0, max_value=1000),
        st.booleans()
    )
)
def test_iovbuffer_unpacking(buffer_type, data):
    """IOVBuffer should support unpacking."""
    buffer = IOVBuffer(type=buffer_type, data=data)
    
    # Test tuple unpacking
    unpacked_type, unpacked_data = buffer
    assert unpacked_type == buffer_type
    assert unpacked_data == data
    
    # Test indexing
    assert buffer[0] == buffer_type
    assert buffer[1] == data
    
    # Test length
    assert len(buffer) == 2


# Advanced test 5: IOVResBuffer with bytes
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    data=st.binary(min_size=0, max_size=10000)
)
def test_iovresbuffer_with_large_bytes(buffer_type, data):
    """IOVResBuffer should handle large byte arrays."""
    buffer = IOVResBuffer(type=buffer_type, data=data)
    assert buffer.type == buffer_type
    assert buffer.data == data
    assert len(buffer) == 2


# Advanced test 6: Test conversion between IOVBuffer and IOVResBuffer
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    data=st.binary(max_size=100)
)
def test_iovbuffer_to_iovresbuffer_conversion(buffer_type, data):
    """Converting IOVBuffer with bytes to IOVResBuffer should work."""
    iov_buffer = IOVBuffer(type=buffer_type, data=data)
    # Create IOVResBuffer with same values
    res_buffer = IOVResBuffer(type=buffer_type, data=data)
    
    # They should have same values but be different types
    assert iov_buffer.type == res_buffer.type
    assert iov_buffer.data == res_buffer.data
    assert type(iov_buffer) != type(res_buffer)


# Advanced test 7: Check for off-by-one errors in BufferType
@given(st.integers(min_value=-1, max_value=4097))
def test_buffertype_boundary_values(value):
    """Test BufferType with boundary values around valid range."""
    valid_values = {0, 1, 2, 3, 7, 9, 10, 11, 12, 4096}
    if value in valid_values:
        bt = BufferType(value)
        assert bt.value == value
    else:
        with pytest.raises(ValueError):
            BufferType(value)


# Advanced test 8: IOVBuffer with None vs empty bytes
@given(buffer_type=st.sampled_from(list(BufferType)))
def test_iovbuffer_none_vs_empty_bytes(buffer_type):
    """IOVBuffer should distinguish between None and empty bytes."""
    buffer_none = IOVBuffer(type=buffer_type, data=None)
    buffer_empty = IOVBuffer(type=buffer_type, data=b"")
    
    assert buffer_none.data is None
    assert buffer_empty.data == b""
    assert buffer_none != buffer_empty
    

# Advanced test 9: Type annotation consistency
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    data=st.one_of(
        st.none(),
        st.binary(max_size=100),
        st.integers(min_value=0, max_value=1000),
        st.booleans()
    )
)
def test_iovbuffer_type_annotation(buffer_type, data):
    """IOVBuffer should accept types as per its annotation."""
    # The annotation says: typing.Optional[typing.Union[bytes, int, bool]]
    buffer = IOVBuffer(type=buffer_type, data=data)
    
    if data is not None:
        assert isinstance(data, (bytes, int, bool))
    assert buffer.data == data


# Advanced test 10: BufferType string representation
@given(st.sampled_from(list(BufferType)))
def test_buffertype_string_representation(buffer_type):
    """BufferType should have expected string representation for IntEnum."""
    # IntEnum's str() returns just the numeric value
    str_repr = str(buffer_type)
    assert str_repr == str(buffer_type.value)
    
    # repr() should have the full enum representation
    repr_str = repr(buffer_type)
    assert "BufferType." in repr_str
    assert buffer_type.name in repr_str


# Advanced test 11: Metamorphic property - creating IOVBuffer multiple ways
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    data=st.one_of(st.none(), st.binary(max_size=100))
)
def test_iovbuffer_creation_methods_equivalent(buffer_type, data):
    """Different ways of creating IOVBuffer should be equivalent."""
    # Direct creation
    buffer1 = IOVBuffer(type=buffer_type, data=data)
    
    # From tuple
    buffer2 = IOVBuffer(*(buffer_type, data))
    
    # Using keyword arguments
    buffer3 = IOVBuffer(data=data, type=buffer_type)
    
    assert buffer1 == buffer2 == buffer3
    assert hash(buffer1) == hash(buffer2) == hash(buffer3)


# Advanced test 12: Check for integer overflow in BufferType
@given(st.integers(min_value=2**31-10, max_value=2**31+10))
def test_buffertype_large_integers(value):
    """BufferType should handle large integers correctly."""
    valid_values = {0, 1, 2, 3, 7, 9, 10, 11, 12, 4096}
    if value in valid_values:
        bt = BufferType(value)
        assert bt.value == value
    else:
        with pytest.raises(ValueError):
            BufferType(value)


# Advanced test 13: IOVBuffer with extreme data sizes
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    size=st.integers(min_value=2**16-10, max_value=2**16+10)
)
def test_iovbuffer_extreme_int_sizes(buffer_type, size):
    """IOVBuffer should handle extreme integer sizes for allocation."""
    buffer = IOVBuffer(type=buffer_type, data=size)
    assert buffer.type == buffer_type
    assert buffer.data == size


# Advanced test 14: Test that BufferType values match documentation
def test_buffertype_matches_windows_gssapi_constants():
    """BufferType values should match documented SSPI/GSSAPI constants."""
    # Based on the comments in the source:
    # empty = 0  # SECBUFFER_EMPTY | GSS_IOV_BUFFER_TYPE_EMPTY
    # data = 1  # SECBUFFER_DATA | GSS_IOV_BUFFER_TYPE_DATA
    # etc.
    
    # These are the known SSPI/GSSAPI constants
    SECBUFFER_EMPTY = 0
    SECBUFFER_DATA = 1
    SECBUFFER_TOKEN = 2
    SECBUFFER_PKG_PARAMS = 3
    SECBUFFER_STREAM_HEADER = 7
    SECBUFFER_PADDING = 9
    SECBUFFER_STREAM = 10
    
    assert BufferType.empty == SECBUFFER_EMPTY
    assert BufferType.data == SECBUFFER_DATA
    assert BufferType.header == SECBUFFER_TOKEN
    assert BufferType.pkg_params == SECBUFFER_PKG_PARAMS
    assert BufferType.trailer == SECBUFFER_STREAM_HEADER
    assert BufferType.padding == SECBUFFER_PADDING
    assert BufferType.stream == SECBUFFER_STREAM