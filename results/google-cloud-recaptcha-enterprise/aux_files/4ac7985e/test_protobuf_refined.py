import json
import math
import struct
from hypothesis import given, strategies as st, assume, settings
from google.protobuf import json_format, text_format
from google.protobuf import wrappers_pb2, struct_pb2, timestamp_pb2, duration_pb2


# Test specifically for float32 boundary issues
@given(st.floats(min_value=3.4e38, max_value=3.5e38, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_json_roundtrip_float_boundary(value):
    """Test FloatValue near the float32 boundary."""
    msg = wrappers_pb2.FloatValue()
    
    # FloatValue uses 32-bit floats internally
    # Convert to float32 and back to see what value actually gets stored
    actual_stored = struct.unpack('f', struct.pack('f', value))[0]
    msg.value = value
    
    # Skip if this produces infinity (out of float32 range)
    if math.isinf(msg.value):
        assume(False)
    
    json_str = json_format.MessageToJson(msg)
    parsed_msg = wrappers_pb2.FloatValue()
    
    try:
        json_format.Parse(json_str, parsed_msg)
        # If parsing succeeds, check the value matches
        assert math.isclose(msg.value, parsed_msg.value, rel_tol=1e-6, abs_tol=1e-9)
    except json_format.ParseError as e:
        if "Float value too large" in str(e):
            # This is the bug - value serializes but can't parse
            print(f"BUG FOUND: Value {msg.value} serializes to '{json_str}' but can't parse back")
            raise
        else:
            raise


# Test double values which should handle larger ranges
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e308, max_value=1e308))
@settings(max_examples=100)
def test_json_roundtrip_double_value(value):
    """Test that DoubleValue can round-trip through JSON."""
    msg = wrappers_pb2.DoubleValue()
    msg.value = value
    
    json_str = json_format.MessageToJson(msg)
    parsed_msg = wrappers_pb2.DoubleValue()
    json_format.Parse(json_str, parsed_msg)
    
    # Double comparison needs tolerance
    assert math.isclose(msg.value, parsed_msg.value, rel_tol=1e-15, abs_tol=1e-308)


# Test edge cases for integers
@given(st.integers(min_value=-2147483648, max_value=2147483647))
@settings(max_examples=100)
def test_text_json_confluence_int32(value):
    """Test that text and JSON formats produce equivalent results."""
    msg = wrappers_pb2.Int32Value()
    msg.value = value
    
    # Convert via JSON
    json_str = json_format.MessageToJson(msg)
    json_parsed = wrappers_pb2.Int32Value()
    json_format.Parse(json_str, json_parsed)
    
    # Convert via text format
    text_str = text_format.MessageToString(msg)
    text_parsed = wrappers_pb2.Int32Value()
    text_format.Parse(text_str, text_parsed)
    
    # Both should produce the same value
    assert json_parsed.value == text_parsed.value == value


# Test that MessageToDict and direct JSON parsing are equivalent
@given(st.text(min_size=0, max_size=1000))
@settings(max_examples=100)
def test_dict_json_equivalence(value):
    """Test that Dict and JSON representations are equivalent."""
    msg = wrappers_pb2.StringValue()
    msg.value = value
    
    # Get dict representation
    dict_repr = json_format.MessageToDict(msg)
    
    # Get JSON and parse it as dict
    json_str = json_format.MessageToJson(msg)
    json_dict = json.loads(json_str)
    
    # They should be the same
    assert dict_repr == json_dict


# Test preservation of field names
@given(st.integers(min_value=-2147483648, max_value=2147483647))
@settings(max_examples=100) 
def test_field_name_preservation(value):
    """Test preserving_proto_field_name option works correctly."""
    msg = wrappers_pb2.Int32Value()
    msg.value = value
    
    # Without preservation (camelCase)
    json_camel = json_format.MessageToJson(msg, preserving_proto_field_name=False)
    
    # With preservation (original names)
    json_preserved = json_format.MessageToJson(msg, preserving_proto_field_name=True)
    
    # Both should parse back correctly
    parsed_camel = wrappers_pb2.Int32Value()
    json_format.Parse(json_camel, parsed_camel)
    
    parsed_preserved = wrappers_pb2.Int32Value()
    json_format.Parse(json_preserved, parsed_preserved)
    
    assert parsed_camel.value == parsed_preserved.value == value


# Test Timestamp edge cases
@given(
    st.integers(min_value=-62135596800, max_value=253402300799),  # Valid range: 0001-01-01 to 9999-12-31
    st.integers(min_value=0, max_value=999999999)
)
@settings(max_examples=100)
def test_timestamp_boundaries(seconds, nanos):
    """Test Timestamp at boundary values."""
    msg = timestamp_pb2.Timestamp()
    msg.seconds = seconds
    msg.nanos = nanos
    
    try:
        json_str = json_format.MessageToJson(msg)
        parsed_msg = timestamp_pb2.Timestamp()
        json_format.Parse(json_str, parsed_msg)
        
        assert msg.seconds == parsed_msg.seconds
        assert msg.nanos == parsed_msg.nanos
    except (ValueError, json_format.Error) as e:
        # Some combinations might be invalid timestamps
        assume(False)


# Test for special float values
@given(st.sampled_from([0.0, -0.0, 1.0, -1.0, 
                        float('inf'), float('-inf'), 
                        1e-45, -1e-45,  # Smallest denormal float32
                        1.175494e-38, -1.175494e-38,  # Smallest normal float32
                        ]))
def test_special_float_values(value):
    """Test special float values."""
    if math.isnan(value) or math.isinf(value):
        # Skip NaN and Inf as they're not valid in JSON by default
        return
        
    msg = wrappers_pb2.FloatValue()
    msg.value = value
    
    json_str = json_format.MessageToJson(msg)
    parsed_msg = wrappers_pb2.FloatValue()
    json_format.Parse(json_str, parsed_msg)
    
    # Check for exact equality for special values like 0.0 and -0.0
    if value == 0.0 or value == -0.0:
        assert math.copysign(1, msg.value) == math.copysign(1, parsed_msg.value)
    else:
        assert math.isclose(msg.value, parsed_msg.value, rel_tol=1e-6, abs_tol=1e-45)