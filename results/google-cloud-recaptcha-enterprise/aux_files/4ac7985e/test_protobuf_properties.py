import json
import math
from hypothesis import given, strategies as st, assume, settings
from google.protobuf import json_format, text_format
from google.protobuf import wrappers_pb2, struct_pb2, timestamp_pb2, duration_pb2


# Strategy for generating valid protobuf values
def protobuf_values():
    """Generate valid values for protobuf Value message."""
    return st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e308, max_value=1e308),
            st.text(min_size=0, max_size=100),
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=10).map(lambda l: {"list": l}),
            st.dictionaries(
                st.text(min_size=1, max_size=50),
                children,
                max_size=10
            ).map(lambda d: {"struct": d})
        ),
        max_leaves=50
    )


# Test 1: JSON round-trip for simple wrapper types
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e308, max_value=1e308))
def test_json_roundtrip_float_value(value):
    """Test that FloatValue can round-trip through JSON."""
    msg = wrappers_pb2.FloatValue()
    msg.value = value
    
    json_str = json_format.MessageToJson(msg)
    parsed_msg = wrappers_pb2.FloatValue()
    json_format.Parse(json_str, parsed_msg)
    
    # Float comparison needs tolerance
    assert math.isclose(msg.value, parsed_msg.value, rel_tol=1e-6, abs_tol=1e-9)


@given(st.integers(min_value=-2147483648, max_value=2147483647))
def test_json_roundtrip_int32_value(value):
    """Test that Int32Value can round-trip through JSON."""
    msg = wrappers_pb2.Int32Value()
    msg.value = value
    
    json_str = json_format.MessageToJson(msg)
    parsed_msg = wrappers_pb2.Int32Value()
    json_format.Parse(json_str, parsed_msg)
    
    assert msg.value == parsed_msg.value


@given(st.text(min_size=0, max_size=1000))
def test_json_roundtrip_string_value(value):
    """Test that StringValue can round-trip through JSON."""
    msg = wrappers_pb2.StringValue()
    msg.value = value
    
    json_str = json_format.MessageToJson(msg)
    parsed_msg = wrappers_pb2.StringValue()
    json_format.Parse(json_str, parsed_msg)
    
    assert msg.value == parsed_msg.value


@given(st.booleans())
def test_json_roundtrip_bool_value(value):
    """Test that BoolValue can round-trip through JSON."""
    msg = wrappers_pb2.BoolValue()
    msg.value = value
    
    json_str = json_format.MessageToJson(msg)
    parsed_msg = wrappers_pb2.BoolValue()
    json_format.Parse(json_str, parsed_msg)
    
    assert msg.value == parsed_msg.value


# Test 2: Dict round-trip for wrapper types
@given(st.integers(min_value=-2147483648, max_value=2147483647))
def test_dict_roundtrip_int32_value(value):
    """Test that Int32Value can round-trip through dict."""
    msg = wrappers_pb2.Int32Value()
    msg.value = value
    
    dict_repr = json_format.MessageToDict(msg)
    parsed_msg = wrappers_pb2.Int32Value()
    json_format.ParseDict(dict_repr, parsed_msg)
    
    assert msg.value == parsed_msg.value


@given(st.text(min_size=0, max_size=1000))
def test_dict_roundtrip_string_value(value):
    """Test that StringValue can round-trip through dict."""
    msg = wrappers_pb2.StringValue()
    msg.value = value
    
    dict_repr = json_format.MessageToDict(msg)
    parsed_msg = wrappers_pb2.StringValue()
    json_format.ParseDict(dict_repr, parsed_msg)
    
    assert msg.value == parsed_msg.value


# Test 3: Text format round-trip
@given(st.integers(min_value=-2147483648, max_value=2147483647))
def test_text_roundtrip_int32_value(value):
    """Test that Int32Value can round-trip through text format."""
    msg = wrappers_pb2.Int32Value()
    msg.value = value
    
    text_str = text_format.MessageToString(msg)
    parsed_msg = wrappers_pb2.Int32Value()
    text_format.Parse(text_str, parsed_msg)
    
    assert msg.value == parsed_msg.value


@given(st.text(min_size=0, max_size=1000))
def test_text_roundtrip_string_value(value):
    """Test that StringValue can round-trip through text format."""
    msg = wrappers_pb2.StringValue()
    msg.value = value
    
    text_str = text_format.MessageToString(msg)
    parsed_msg = wrappers_pb2.StringValue()
    text_format.Parse(text_str, parsed_msg)
    
    assert msg.value == parsed_msg.value


# Test 4: Struct Value round-trip (more complex)
@given(protobuf_values())
def test_json_roundtrip_struct_value(value):
    """Test that Struct Value can round-trip through JSON."""
    msg = struct_pb2.Value()
    
    if value is None:
        msg.null_value = struct_pb2.NULL_VALUE
    elif isinstance(value, bool):
        msg.bool_value = value
    elif isinstance(value, (int, float)):
        msg.number_value = float(value)
    elif isinstance(value, str):
        msg.string_value = value
    elif isinstance(value, dict):
        if "list" in value:
            for item in value["list"]:
                list_value = msg.list_value.values.add()
                set_value(list_value, item)
        elif "struct" in value:
            for key, val in value["struct"].items():
                set_value(msg.struct_value.fields[key], val)
    
    json_str = json_format.MessageToJson(msg)
    parsed_msg = struct_pb2.Value()
    json_format.Parse(json_str, parsed_msg)
    
    # Convert both back to JSON for comparison (easier than deep message comparison)
    assert json_format.MessageToJson(msg) == json_format.MessageToJson(parsed_msg)


def set_value(msg, value):
    """Helper to set a Value message."""
    if value is None:
        msg.null_value = struct_pb2.NULL_VALUE
    elif isinstance(value, bool):
        msg.bool_value = value
    elif isinstance(value, (int, float)):
        msg.number_value = float(value)
    elif isinstance(value, str):
        msg.string_value = value
    elif isinstance(value, dict):
        if "list" in value:
            for item in value["list"]:
                list_value = msg.list_value.values.add()
                set_value(list_value, item)
        elif "struct" in value:
            for key, val in value["struct"].items():
                set_value(msg.struct_value.fields[key], val)


# Test 5: Timestamp round-trip
@given(
    st.integers(min_value=0, max_value=253402300799),  # Valid Unix timestamp range
    st.integers(min_value=0, max_value=999999999)  # Valid nanoseconds
)
def test_json_roundtrip_timestamp(seconds, nanos):
    """Test that Timestamp can round-trip through JSON."""
    msg = timestamp_pb2.Timestamp()
    msg.seconds = seconds
    msg.nanos = nanos
    
    json_str = json_format.MessageToJson(msg)
    parsed_msg = timestamp_pb2.Timestamp()
    json_format.Parse(json_str, parsed_msg)
    
    assert msg.seconds == parsed_msg.seconds
    assert msg.nanos == parsed_msg.nanos


# Test 6: Duration round-trip
@given(
    st.integers(min_value=-315576000000, max_value=315576000000),  # +/- 10000 years in seconds
    st.integers(min_value=-999999999, max_value=999999999)  # Valid nanoseconds
)
def test_json_roundtrip_duration(seconds, nanos):
    """Test that Duration can round-trip through JSON."""
    # Duration requires that nanos have the same sign as seconds
    if seconds > 0 and nanos < 0:
        nanos = -nanos
    elif seconds < 0 and nanos > 0:
        nanos = -nanos
    
    msg = duration_pb2.Duration()
    msg.seconds = seconds
    msg.nanos = nanos
    
    json_str = json_format.MessageToJson(msg)
    parsed_msg = duration_pb2.Duration()
    json_format.Parse(json_str, parsed_msg)
    
    assert msg.seconds == parsed_msg.seconds
    assert msg.nanos == parsed_msg.nanos


# Test 7: Confluence property - JSON and Dict should produce same result
@given(st.integers(min_value=-2147483648, max_value=2147483647))
def test_json_dict_confluence_int32(value):
    """Test that JSON and Dict parsing produce the same message."""
    msg = wrappers_pb2.Int32Value()
    msg.value = value
    
    # Convert to JSON and Dict
    json_str = json_format.MessageToJson(msg)
    dict_repr = json_format.MessageToDict(msg)
    
    # Parse from JSON
    json_parsed = wrappers_pb2.Int32Value()
    json_format.Parse(json_str, json_parsed)
    
    # Parse from Dict
    dict_parsed = wrappers_pb2.Int32Value()
    json_format.ParseDict(dict_repr, dict_parsed)
    
    # Both should produce the same result
    assert json_parsed.value == dict_parsed.value == value


# Test 8: Special characters in strings
@given(st.text(alphabet=st.characters(whitelist_categories=["Cc", "Cf", "Cn", "Co", "Cs"]), min_size=0, max_size=100))
def test_json_roundtrip_control_characters(value):
    """Test that strings with control characters can round-trip."""
    msg = wrappers_pb2.StringValue()
    msg.value = value
    
    json_str = json_format.MessageToJson(msg)
    parsed_msg = wrappers_pb2.StringValue()
    json_format.Parse(json_str, parsed_msg)
    
    assert msg.value == parsed_msg.value


# Test 9: Unicode strings
@given(st.text(alphabet=st.characters(min_codepoint=0x1F600, max_codepoint=0x1F64F), min_size=0, max_size=50))
def test_json_roundtrip_emoji(value):
    """Test that emoji strings can round-trip through JSON."""
    msg = wrappers_pb2.StringValue()
    msg.value = value
    
    json_str = json_format.MessageToJson(msg)
    parsed_msg = wrappers_pb2.StringValue()
    json_format.Parse(json_str, parsed_msg)
    
    assert msg.value == parsed_msg.value