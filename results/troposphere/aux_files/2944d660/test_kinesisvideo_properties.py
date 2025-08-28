#!/usr/bin/env python3
"""Property-based tests for troposphere.kinesisvideo module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere.kinesisvideo import SignalingChannel, Stream
from troposphere.validators import integer


# Test the integer validator function
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x)),
    st.text(min_size=1).filter(lambda s: s.strip().lstrip('-').isdigit()),
))
def test_integer_validator_type_preservation(value):
    """The integer validator should preserve the type of valid input."""
    result = integer(value)
    # The validator should return the original value, not a converted int
    assert result is value
    # But it should be convertible to int
    int(result)


@given(st.one_of(
    st.text(min_size=1).filter(lambda s: not s.strip().lstrip('-').replace('.', '', 1).isdigit()),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
))
def test_integer_validator_invalid_input(value):
    """The integer validator should raise ValueError for non-integer values."""
    # Skip values that might actually be valid integers
    try:
        int(value)
        assume(False)  # Skip if it can be converted to int
    except (ValueError, TypeError):
        pass
    
    with pytest.raises(ValueError):
        integer(value)


@given(
    st.integers(min_value=0, max_value=999999),
    st.text(min_size=1, max_size=50).filter(lambda s: s.isalnum()),
)
def test_signaling_channel_message_ttl_property(ttl, name):
    """SignalingChannel should accept valid integer TTL values."""
    # Test with integer
    channel = SignalingChannel("TestChannel", MessageTtlSeconds=ttl, Name=name)
    assert channel.MessageTtlSeconds == ttl
    
    # Test with string representation of integer
    str_ttl = str(ttl)
    channel2 = SignalingChannel("TestChannel2", MessageTtlSeconds=str_ttl, Name=name)
    assert channel2.MessageTtlSeconds == str_ttl
    # The value should still be convertible to int
    assert int(channel2.MessageTtlSeconds) == ttl


@given(
    st.integers(min_value=0, max_value=999999),
    st.text(min_size=1, max_size=50).filter(lambda s: s.isalnum()),
)
def test_stream_data_retention_property(hours, name):
    """Stream should accept valid integer retention hours."""
    # Test with integer
    stream = Stream("TestStream", DataRetentionInHours=hours, Name=name)
    assert stream.DataRetentionInHours == hours
    
    # Test with string representation
    str_hours = str(hours)
    stream2 = Stream("TestStream2", DataRetentionInHours=str_hours, Name=name)
    assert stream2.DataRetentionInHours == str_hours
    assert int(stream2.DataRetentionInHours) == hours


@given(
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)),
)
def test_integer_property_rejects_non_integers(value):
    """Properties expecting integers should reject non-integer floats."""
    # SignalingChannel.MessageTtlSeconds should reject non-integer floats
    with pytest.raises(ValueError):
        SignalingChannel("TestChannel", MessageTtlSeconds=value)
    
    # Stream.DataRetentionInHours should reject non-integer floats
    with pytest.raises(ValueError):
        Stream("TestStream", DataRetentionInHours=value)


@given(st.text(min_size=1, max_size=50).filter(lambda s: s.isalnum()))
def test_object_to_dict_preserves_properties(name):
    """Converting objects to dict should preserve their properties."""
    # Test SignalingChannel
    ttl = 300
    channel = SignalingChannel("TestChannel", MessageTtlSeconds=ttl, Name=name, Type="SINGLE_MASTER")
    channel_dict = channel.to_dict()
    
    assert "Properties" in channel_dict
    assert channel_dict["Properties"]["MessageTtlSeconds"] == ttl
    assert channel_dict["Properties"]["Name"] == name
    assert channel_dict["Properties"]["Type"] == "SINGLE_MASTER"
    
    # Test Stream
    hours = 24
    stream = Stream("TestStream", DataRetentionInHours=hours, Name=name, MediaType="video/h264")
    stream_dict = stream.to_dict()
    
    assert "Properties" in stream_dict
    assert stream_dict["Properties"]["DataRetentionInHours"] == hours
    assert stream_dict["Properties"]["Name"] == name
    assert stream_dict["Properties"]["MediaType"] == "video/h264"


# Test for potential type confusion bug
@given(st.one_of(
    st.just("123"),
    st.just("456"),
    st.just(123),
    st.just(456),
))
def test_integer_validator_string_int_equivalence(value):
    """Test that string and int representations are handled consistently."""
    result = integer(value)
    # Should preserve the original type
    assert type(result) == type(value)
    
    # When used in objects, should preserve type
    channel = SignalingChannel("Test", MessageTtlSeconds=value)
    assert type(channel.MessageTtlSeconds) == type(value)
    assert channel.MessageTtlSeconds == value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])