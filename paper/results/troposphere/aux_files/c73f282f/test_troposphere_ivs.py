#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""Property-based tests for troposphere.ivs module"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import math
import re

# Import modules to test
from troposphere import ivs
from troposphere.validators import boolean, integer, double, s3_bucket_name, network_port, integer_range


# Test 1: Boolean validator properties
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator accepts documented valid inputs"""
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(
    st.text().filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(allow_nan=False, allow_infinity=False),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator rejects non-boolean inputs"""
    with pytest.raises(ValueError):
        boolean(value)


# Test 2: Integer validator properties  
@given(st.one_of(
    st.integers(),
    st.text().map(str).filter(lambda x: x.lstrip('-').isdigit()),
))
def test_integer_validator_valid(value):
    """Test that integer validator accepts integer-convertible values"""
    result = integer(value)
    # Should return the original value
    assert result == value
    # Should be convertible to int
    int(result)


@given(st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).filter(lambda x: not x.is_integer() if not math.isnan(x) and not math.isinf(x) else True),
    st.text().filter(lambda x: not x.lstrip('-').replace('.', '', 1).isdigit() and not x.lstrip('-').isdigit()),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator_invalid(value):
    """Test that integer validator rejects non-integer values"""
    with pytest.raises(ValueError):
        integer(value)


# Test 3: Double validator properties
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text().filter(lambda x: x.replace('.', '', 1).replace('-', '', 1).replace('e', '', 1).replace('+', '', 1).isdigit() if x else False),
))
def test_double_validator_valid(value):
    """Test that double validator accepts float-convertible values"""
    try:
        float(value)  # Pre-check if it's convertible
    except (ValueError, TypeError):
        assume(False)  # Skip this value
    
    result = double(value)
    assert result == value
    # Should be convertible to float
    float(result)


@given(st.one_of(
    st.text().filter(lambda x: not x.replace('.', '', 1).replace('-', '', 1).replace('e', '', 1).replace('+', '', 1).isdigit() if x else True),
    st.lists(st.floats()),
    st.dictionaries(st.text(), st.floats())
))
def test_double_validator_invalid(value):
    """Test that double validator rejects non-float values"""
    # Skip values that are actually valid floats
    try:
        float(value)
        assume(False)
    except (ValueError, TypeError):
        pass
    
    with pytest.raises(ValueError):
        double(value)


# Test 4: Network port validator
@given(st.integers(min_value=-1, max_value=65535))
def test_network_port_valid_range(port):
    """Test that network_port accepts valid port numbers"""
    result = network_port(port)
    assert result == port


@given(st.one_of(
    st.integers(max_value=-2),
    st.integers(min_value=65536)
))
def test_network_port_invalid_range(port):
    """Test that network_port rejects out-of-range port numbers"""
    with pytest.raises(ValueError, match="network port .* must been between 0 and 65535"):
        network_port(port)


# Test 5: S3 bucket name validator
@given(st.text(min_size=3, max_size=63, alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='.-')))
def test_s3_bucket_name_properties(name):
    """Test S3 bucket name validation properties"""
    # Apply the documented rules
    is_valid = True
    
    # Rule 1: No consecutive periods
    if '..' in name:
        is_valid = False
    
    # Rule 2: Not an IP address
    ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    if ip_pattern.match(name):
        is_valid = False
    
    # Rule 3: Must match the pattern
    bucket_pattern = re.compile(r'^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$')
    if not bucket_pattern.match(name):
        is_valid = False
    
    # Test the validator
    if is_valid:
        result = s3_bucket_name(name)
        assert result == name
    else:
        with pytest.raises(ValueError):
            s3_bucket_name(name)


# Test 6: Integer range validator
@given(
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=-2000, max_value=2000)
)
def test_integer_range_validator(min_val, max_val, test_val):
    """Test integer_range validator factory function"""
    assume(min_val <= max_val)  # Ensure valid range
    
    validator = integer_range(min_val, max_val)
    
    if min_val <= test_val <= max_val:
        result = validator(test_val)
        assert result == test_val
    else:
        with pytest.raises(ValueError, match="Integer must be between"):
            validator(test_val)


# Test 7: IVS Video class properties
@given(
    bitrate=st.one_of(st.none(), st.integers(min_value=1, max_value=10000000)),
    framerate=st.one_of(st.none(), st.floats(min_value=1.0, max_value=120.0, allow_nan=False)),
    height=st.one_of(st.none(), st.integers(min_value=1, max_value=4096)),
    width=st.one_of(st.none(), st.integers(min_value=1, max_value=4096))
)
def test_ivs_video_class_creation(bitrate, framerate, height, width):
    """Test that Video class correctly validates its properties"""
    kwargs = {}
    if bitrate is not None:
        kwargs['Bitrate'] = bitrate
    if framerate is not None:
        kwargs['Framerate'] = framerate
    if height is not None:
        kwargs['Height'] = height
    if width is not None:
        kwargs['Width'] = width
    
    # Should create without errors
    video = ivs.Video(**kwargs)
    
    # Check properties are set correctly
    if bitrate is not None:
        assert video.Bitrate == bitrate
    if framerate is not None:
        assert video.Framerate == framerate
    if height is not None:
        assert video.Height == height
    if width is not None:
        assert video.Width == width
    
    # Test to_dict round-trip
    video_dict = video.to_dict()
    assert isinstance(video_dict, dict)
    
    # Properties should be in the dict
    if bitrate is not None:
        assert video_dict['Bitrate'] == bitrate
    if framerate is not None:
        assert video_dict['Framerate'] == framerate


# Test 8: IVS Channel class with boolean properties
@given(
    authorized=st.one_of(st.none(), st.booleans()),
    insecure_ingest=st.one_of(st.none(), st.booleans()),
    name=st.one_of(st.none(), st.text(min_size=1, max_size=128))
)
def test_ivs_channel_boolean_properties(authorized, insecure_ingest, name):
    """Test that Channel class correctly handles boolean properties"""
    kwargs = {}
    if authorized is not None:
        kwargs['Authorized'] = authorized
    if insecure_ingest is not None:
        kwargs['InsecureIngest'] = insecure_ingest
    if name is not None:
        kwargs['Name'] = name
    
    # Should create without errors
    channel = ivs.Channel("TestChannel", **kwargs)
    
    # Check properties
    if authorized is not None:
        assert channel.Authorized == authorized
    if insecure_ingest is not None:
        assert channel.InsecureIngest == insecure_ingest
    if name is not None:
        assert channel.Name == name
    
    # Test serialization
    channel_dict = channel.to_dict()
    assert channel_dict['Type'] == 'AWS::IVS::Channel'


# Test 9: Property validation with invalid types
@given(
    value=st.one_of(
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers()),
        st.text(min_size=1)
    )
)
def test_ivs_video_invalid_integer_property(value):
    """Test that Video class rejects invalid integer values"""
    # Skip values that might be valid integers
    try:
        int(value)
        assume(False)
    except (ValueError, TypeError):
        pass
    
    with pytest.raises((TypeError, ValueError)):
        ivs.Video(Bitrate=value)


# Test 10: Required vs optional properties
def test_ivs_required_properties():
    """Test that required properties are enforced"""
    # PlaybackRestrictionPolicy has required properties
    with pytest.raises(TypeError):
        # Missing required AllowedCountries
        policy = ivs.PlaybackRestrictionPolicy("TestPolicy", AllowedOrigins=["https://example.com"])
    
    with pytest.raises(TypeError):
        # Missing required AllowedOrigins  
        policy = ivs.PlaybackRestrictionPolicy("TestPolicy", AllowedCountries=["US"])
    
    # Should work with both required properties
    policy = ivs.PlaybackRestrictionPolicy(
        "TestPolicy",
        AllowedCountries=["US", "CA"],
        AllowedOrigins=["https://example.com"]
    )
    
    policy_dict = policy.to_dict()
    assert policy_dict['Type'] == 'AWS::IVS::PlaybackRestrictionPolicy'
    assert policy_dict['Properties']['AllowedCountries'] == ["US", "CA"]
    assert policy_dict['Properties']['AllowedOrigins'] == ["https://example.com"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])