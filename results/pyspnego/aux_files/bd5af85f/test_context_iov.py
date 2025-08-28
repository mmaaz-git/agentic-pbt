import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from spnego.iov import BufferType, IOVBuffer, IOVResBuffer


# Test the _build_iov_list logic from _context.py
# Simulating the validation logic from that function

def validate_iov_entry(entry):
    """Simulate the validation logic from _build_iov_list."""
    if isinstance(entry, tuple):
        if len(entry) != 2:
            raise ValueError("IOV entry tuple must contain 2 values, the type and data, see IOVBuffer.")
        
        if not isinstance(entry[0], int):
            raise ValueError("IOV entry[0] must specify the BufferType as an int")
        
        buffer_type = entry[0]
        
        if entry[1] is not None and not isinstance(entry[1], (bytes, int, bool)):
            raise ValueError(
                "IOV entry[1] must specify the buffer bytes, length of the buffer, or whether "
                "it is auto allocated."
            )
        data = entry[1] if entry[1] is not None else b""
        
    elif isinstance(entry, int):
        buffer_type = entry
        data = None
        
    elif isinstance(entry, bytes):
        buffer_type = BufferType.data
        data = entry
        
    else:
        raise ValueError("IOV entry must be a IOVBuffer tuple, int, or bytes")
    
    # This will raise ValueError if buffer_type is not valid
    return IOVBuffer(type=BufferType(buffer_type), data=data)


# Test 1: Invalid tuple sizes
@given(
    tuple_size=st.integers(min_value=0, max_value=10).filter(lambda x: x != 2),
    elements=st.lists(st.integers(), min_size=0, max_size=10)
)
def test_invalid_tuple_size(tuple_size, elements):
    """Tuples with size != 2 should raise ValueError."""
    # Ensure we have exactly tuple_size elements
    while len(elements) < tuple_size:
        elements.append(0)
    elements = elements[:tuple_size]
    
    entry = tuple(elements)
    with pytest.raises(ValueError, match="IOV entry tuple must contain 2 values"):
        validate_iov_entry(entry)


# Test 2: Non-integer first element in tuple
@given(
    first_elem=st.one_of(
        st.text(min_size=1),
        st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)),
        st.lists(st.integers(), min_size=1),
        st.dictionaries(st.text(), st.integers(), min_size=1)
    ),
    second_elem=st.one_of(st.none(), st.binary())
)
def test_non_integer_buffer_type(first_elem, second_elem):
    """Non-integer buffer type should raise ValueError."""
    entry = (first_elem, second_elem)
    with pytest.raises(ValueError, match="IOV entry\\[0\\] must specify the BufferType as an int"):
        validate_iov_entry(entry)


# Test 3: Invalid data types in second element
@given(
    buffer_type=st.integers(min_value=0, max_value=4096),
    invalid_data=st.one_of(
        st.text(min_size=1),
        st.floats(allow_nan=False, allow_infinity=False),
        st.lists(st.integers(), min_size=1),
        st.dictionaries(st.text(), st.integers(), min_size=1)
    )
)
def test_invalid_data_type(buffer_type, invalid_data):
    """Invalid data types should raise ValueError."""
    entry = (buffer_type, invalid_data)
    with pytest.raises(ValueError, match="IOV entry\\[1\\] must specify"):
        validate_iov_entry(entry)


# Test 4: Edge case - empty tuple
def test_empty_tuple():
    """Empty tuple should raise ValueError."""
    entry = ()
    with pytest.raises(ValueError, match="IOV entry tuple must contain 2 values"):
        validate_iov_entry(entry)


# Test 5: Edge case - single element tuple
@given(st.integers())
def test_single_element_tuple(value):
    """Single element tuple should raise ValueError."""
    entry = (value,)
    with pytest.raises(ValueError, match="IOV entry tuple must contain 2 values"):
        validate_iov_entry(entry)


# Test 6: Invalid BufferType values
@given(
    invalid_buffer_type=st.integers().filter(lambda x: x not in {0, 1, 2, 3, 7, 9, 10, 11, 12, 4096}),
    data=st.one_of(st.none(), st.binary())
)
def test_invalid_buffer_type_value(invalid_buffer_type, data):
    """Invalid BufferType values should raise ValueError."""
    entry = (invalid_buffer_type, data)
    with pytest.raises(ValueError):
        validate_iov_entry(entry)


# Test 7: None data is converted to empty bytes
@given(buffer_type=st.sampled_from([0, 1, 2, 3, 7, 9, 10, 11, 12, 4096]))
def test_none_data_conversion(buffer_type):
    """None data should be converted to empty bytes in tuples."""
    entry = (buffer_type, None)
    result = validate_iov_entry(entry)
    assert result.type == BufferType(buffer_type)
    assert result.data == b""  # None is converted to b""


# Test 8: Direct integer input
@given(buffer_type=st.sampled_from([0, 1, 2, 3, 7, 9, 10, 11, 12, 4096]))
def test_direct_integer_input(buffer_type):
    """Direct integer input should work."""
    result = validate_iov_entry(buffer_type)
    assert result.type == BufferType(buffer_type)
    assert result.data is None


# Test 9: Direct bytes input
@given(data=st.binary())
def test_direct_bytes_input(data):
    """Direct bytes input should use BufferType.data."""
    result = validate_iov_entry(data)
    assert result.type == BufferType.data
    assert result.data == data


# Test 10: Invalid input types
@given(
    invalid_input=st.one_of(
        st.text(min_size=1),
        st.floats(allow_nan=False, allow_infinity=False),
        st.dictionaries(st.text(), st.integers(), min_size=1),
        st.sets(st.integers(), min_size=1)
    )
)
def test_invalid_input_types(invalid_input):
    """Invalid input types should raise ValueError."""
    with pytest.raises(ValueError, match="IOV entry must be"):
        validate_iov_entry(invalid_input)


# Test 11: Boolean in buffer type position
@given(
    bool_type=st.booleans(),
    data=st.one_of(st.none(), st.binary())
)
def test_boolean_as_buffer_type(bool_type, data):
    """Boolean as buffer type (coerces to 0 or 1)."""
    entry = (bool_type, data)
    result = validate_iov_entry(entry)
    # True -> 1 (BufferType.data), False -> 0 (BufferType.empty)
    if bool_type:
        assert result.type == BufferType.data
    else:
        assert result.type == BufferType.empty
    expected_data = data if data is not None else b""
    assert result.data == expected_data


# Test 12: Float that equals integer as buffer type
@given(
    buffer_type_float=st.sampled_from([0.0, 1.0, 2.0, 3.0, 7.0, 9.0, 10.0, 11.0, 12.0, 4096.0]),
    data=st.binary(max_size=10)
)
def test_float_as_buffer_type(buffer_type_float, data):
    """Float that equals an integer might work as buffer type."""
    entry = (buffer_type_float, data)
    # The validation checks isinstance(entry[0], int) which should fail for float
    with pytest.raises(ValueError, match="IOV entry\\[0\\] must specify the BufferType as an int"):
        validate_iov_entry(entry)