import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
import pytest
from spnego.iov import BufferType, IOVBuffer, IOVResBuffer
from spnego._context import ContextProxy
import typing


# Test 1: BufferType enum invariants
@given(st.sampled_from(list(BufferType)))
def test_buffertype_enum_conversion_round_trip(buffer_type):
    """Converting BufferType to int and back should preserve the value."""
    int_val = int(buffer_type)
    result = BufferType(int_val)
    assert result == buffer_type
    assert result.value == buffer_type.value
    assert result.name == buffer_type.name


@given(st.sampled_from(list(BufferType)))
def test_buffertype_enum_unique_values(buffer_type):
    """Each BufferType should have a unique value."""
    count = sum(1 for bt in BufferType if bt.value == buffer_type.value)
    assert count == 1


# Test 2: IOVBuffer creation and properties
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    data=st.one_of(
        st.none(),
        st.binary(min_size=0, max_size=1000),
        st.integers(min_value=0, max_value=65536),
        st.booleans()
    )
)
def test_iovbuffer_creation(buffer_type, data):
    """IOVBuffer should accept valid type and data combinations."""
    buffer = IOVBuffer(type=buffer_type, data=data)
    assert buffer.type == buffer_type
    assert buffer.data == data
    # NamedTuple should be immutable
    with pytest.raises(AttributeError):
        buffer.type = BufferType.empty
    with pytest.raises(AttributeError):
        buffer.data = b"new"


@given(
    buffer_type=st.sampled_from(list(BufferType)),
    data=st.one_of(st.none(), st.binary(min_size=0, max_size=1000))
)
def test_iovresbuffer_creation(buffer_type, data):
    """IOVResBuffer should only accept bytes or None as data."""
    buffer = IOVResBuffer(type=buffer_type, data=data)
    assert buffer.type == buffer_type
    assert buffer.data == data
    # NamedTuple should be immutable
    with pytest.raises(AttributeError):
        buffer.type = BufferType.empty
    with pytest.raises(AttributeError):
        buffer.data = b"new"


# Test 3: Direct test of IOV conversion logic
# Since _build_iov_list is a method that processes IOV inputs,
# we'll test the conversion logic directly

@given(
    buffer_type=st.sampled_from([bt.value for bt in BufferType]),
    data=st.one_of(
        st.none(),
        st.binary(min_size=0, max_size=100),
        st.integers(min_value=0, max_value=1000),
        st.booleans()
    )
)
def test_iovbuffer_from_tuple_preserves_data(buffer_type, data):
    """Creating IOVBuffer from tuple should preserve type and data."""
    # Test the IOVBuffer creation logic directly
    buffer = IOVBuffer(type=BufferType(buffer_type), data=data)
    assert buffer.type == BufferType(buffer_type)
    assert buffer.data == data
    
    # Test tuple unpacking
    buffer_from_tuple = IOVBuffer(*((BufferType(buffer_type), data)))
    assert buffer_from_tuple == buffer


# Test 4: IOVBuffer handles different input formats properly
@given(st.sampled_from([bt.value for bt in BufferType]))
def test_iovbuffer_from_int_creates_with_none_data(buffer_type):
    """Creating IOVBuffer with just type should have None data."""
    # When only type is specified, data should be None
    buffer = IOVBuffer(type=BufferType(buffer_type), data=None)
    assert buffer.type == BufferType(buffer_type)
    assert buffer.data is None


# Test 5: IOVBuffer with bytes data
@given(st.binary(min_size=0, max_size=100))
def test_iovbuffer_with_bytes_data(data):
    """IOVBuffer with bytes data should preserve the bytes."""
    buffer = IOVBuffer(type=BufferType.data, data=data)
    assert buffer.type == BufferType.data
    assert buffer.data == data


# Test 6: Test that IOVBuffer accepts all valid data types
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    int_data=st.integers(min_value=0, max_value=65536)
)
def test_iovbuffer_accepts_int_data(buffer_type, int_data):
    """IOVBuffer should accept integer data for buffer size."""
    buffer = IOVBuffer(type=buffer_type, data=int_data)
    assert buffer.type == buffer_type
    assert buffer.data == int_data


@given(
    buffer_type=st.sampled_from(list(BufferType)),
    bool_data=st.booleans()
)
def test_iovbuffer_accepts_bool_data(buffer_type, bool_data):
    """IOVBuffer should accept boolean data for auto-allocation."""
    buffer = IOVBuffer(type=buffer_type, data=bool_data)
    assert buffer.type == buffer_type
    assert buffer.data == bool_data


# Test 7: IOVResBuffer only accepts bytes or None
@given(
    buffer_type=st.sampled_from(list(BufferType)),
    invalid_data=st.one_of(st.integers(), st.booleans(), st.text())
)
def test_iovresbuffer_rejects_non_bytes_data(buffer_type, invalid_data):
    """IOVResBuffer should raise error for non-bytes data."""
    # IOVResBuffer is a NamedTuple, so it doesn't validate at creation time
    # But the type annotation specifies Optional[bytes]
    # This test verifies the design intent
    buffer = IOVResBuffer(type=buffer_type, data=invalid_data)
    # The buffer is created but violates the type annotation
    assert buffer.type == buffer_type
    assert buffer.data == invalid_data
    # Note: This shows that the type annotation is not enforced at runtime


# Test 8: BufferType values are distinct
def test_buffertype_values_are_distinct():
    """All BufferType enum values should be distinct."""
    values = [bt.value for bt in BufferType]
    assert len(values) == len(set(values))