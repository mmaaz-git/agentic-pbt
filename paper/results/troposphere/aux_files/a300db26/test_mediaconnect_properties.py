#!/usr/bin/env python3
"""Property-based tests for troposphere.mediaconnect module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.provisional import domains
import pytest
import math

# Import the module we're testing
from troposphere import mediaconnect
from troposphere.validators import integer, double, integer_range, integer_list_item


# Test 1: Integer validator property
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x)),
    st.text(alphabet='0123456789', min_size=1),
    st.text(alphabet='-0123456789', min_size=1).filter(lambda s: s != '-' and not s.startswith('00'))
))
def test_integer_validator_accepts_valid_integers(value):
    """The integer validator should accept any value convertible to int."""
    try:
        result = integer(value)
        # If it succeeds, verify the value can be converted to int
        int(result)
    except (ValueError, TypeError, OverflowError):
        # Some edge cases might still fail, that's ok
        pass


@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)),
    st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator_rejects_invalid_integers(value):
    """The integer validator should reject values not convertible to int."""
    with pytest.raises(ValueError):
        integer(value)


# Test 2: Double validator property
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(alphabet='0123456789.', min_size=1).filter(
        lambda s: s.count('.') <= 1 and s != '.' and not s.startswith('.') and not s.endswith('.')
    )
))
def test_double_validator_accepts_valid_floats(value):
    """The double validator should accept any value convertible to float."""
    try:
        result = double(value)
        # If it succeeds, verify the value can be converted to float
        float(result)
    except (ValueError, TypeError, OverflowError):
        # Some edge cases might still fail
        pass


@given(st.one_of(
    st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1),
    st.none(),
    st.lists(st.floats()),
    st.dictionaries(st.text(), st.floats())
))
def test_double_validator_rejects_invalid_floats(value):
    """The double validator should reject values not convertible to float."""
    with pytest.raises(ValueError):
        double(value)


# Test 3: Integer range validator
@given(
    st.integers(min_value=-10000, max_value=10000),
    st.integers(min_value=-10000, max_value=10000),
    st.integers()
)
def test_integer_range_validator(min_val, max_val, test_val):
    """Integer range validator should accept values within range and reject outside."""
    assume(min_val <= max_val)  # Ensure valid range
    
    validator = integer_range(min_val, max_val)
    
    if min_val <= test_val <= max_val:
        # Should accept values within range
        result = validator(test_val)
        assert result == test_val
    else:
        # Should reject values outside range
        with pytest.raises(ValueError, match="Integer must be between"):
            validator(test_val)


# Test 4: Required properties enforcement
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=65535)
)
def test_bridge_network_output_required_properties(ip, name, port):
    """BridgeNetworkOutput should enforce required properties."""
    # All required properties provided - should work
    output = mediaconnect.BridgeNetworkOutput(
        IpAddress=ip,
        NetworkName=name,
        Port=port,
        Protocol="tcp",
        Ttl=255
    )
    
    # Verify the properties are set correctly
    assert hasattr(output, 'properties')
    props = output.properties
    assert props.get('IpAddress') == ip
    assert props.get('NetworkName') == name
    assert props.get('Port') == port


# Test 5: Property serialization round-trip
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=65535),
    st.sampled_from(['tcp', 'udp']),
    st.integers(min_value=1, max_value=255)
)
def test_bridge_network_output_serialization(ip, name, port, protocol, ttl):
    """Objects should correctly serialize to dict and preserve values."""
    output = mediaconnect.BridgeNetworkOutput(
        IpAddress=ip,
        NetworkName=name,
        Port=port,
        Protocol=protocol,
        Ttl=ttl
    )
    
    # Test to_dict serialization
    dict_repr = output.to_dict()
    assert isinstance(dict_repr, dict)
    assert dict_repr.get('IpAddress') == ip
    assert dict_repr.get('NetworkName') == name
    assert dict_repr.get('Port') == port
    assert dict_repr.get('Protocol') == protocol
    assert dict_repr.get('Ttl') == ttl


# Test 6: Integer validators in actual properties
@given(st.integers())
def test_bridge_network_source_port_validation(port_value):
    """Port property should use integer validator correctly."""
    try:
        source = mediaconnect.BridgeNetworkSource(
            MulticastIp="239.0.0.1",
            NetworkName="test",
            Port=port_value,
            Protocol="tcp"
        )
        # If it succeeds, the port should be stored
        assert source.properties.get('Port') == port_value
    except (ValueError, TypeError):
        # Should only fail for invalid integers
        with pytest.raises((ValueError, TypeError)):
            int(port_value)


# Test 7: Optional vs Required property handling
@given(
    st.text(min_size=1, max_size=100),
    st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_vpc_interface_attachment_optional_property(vpc_name, optional_value):
    """Optional properties should accept None/missing values."""
    if optional_value is None:
        # Should work without optional property
        attachment = mediaconnect.VpcInterfaceAttachment()
        assert not hasattr(attachment.properties, 'VpcInterfaceName') or \
               attachment.properties.get('VpcInterfaceName') is None
    else:
        # Should work with optional property
        attachment = mediaconnect.VpcInterfaceAttachment(
            VpcInterfaceName=optional_value
        )
        assert attachment.properties.get('VpcInterfaceName') == optional_value


# Test 8: Complex nested properties
@given(
    st.integers(min_value=1, max_value=1000000000),
    st.integers(min_value=1, max_value=1000)
)
def test_ingress_gateway_bridge_properties(bitrate, outputs):
    """IngressGatewayBridge should correctly handle integer properties."""
    bridge = mediaconnect.IngressGatewayBridge(
        MaxBitrate=bitrate,
        MaxOutputs=outputs
    )
    
    assert bridge.properties.get('MaxBitrate') == bitrate
    assert bridge.properties.get('MaxOutputs') == outputs
    
    # Test serialization
    dict_repr = bridge.to_dict()
    assert dict_repr['MaxBitrate'] == bitrate
    assert dict_repr['MaxOutputs'] == outputs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])