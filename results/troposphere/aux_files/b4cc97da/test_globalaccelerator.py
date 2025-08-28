#!/usr/bin/env python3
"""Property-based tests for troposphere.globalaccelerator module."""

import sys
import json
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the troposphere environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.globalaccelerator import (
    Accelerator, 
    EndpointGroup,
    Listener,
    PortRange,
    EndpointConfiguration,
    PortOverride,
    CrossAccountAttachment,
    Resource
)
from troposphere.validators.globalaccelerator import (
    accelerator_ipaddresstype,
    endpointgroup_healthcheckprotocol,
    listener_clientaffinity,
    listener_protocol,
)


# Test 1: Validator functions should accept valid values and reject invalid ones
@given(st.text())
def test_accelerator_ipaddresstype_validator(value):
    """Test that accelerator_ipaddresstype only accepts valid values."""
    valid_types = ["IPV4"]
    if value in valid_types:
        assert accelerator_ipaddresstype(value) == value
    else:
        with pytest.raises(ValueError) as exc_info:
            accelerator_ipaddresstype(value)
        assert 'IpAddressType must be one of: "IPV4"' in str(exc_info.value)


@given(st.text())
def test_endpointgroup_healthcheckprotocol_validator(value):
    """Test that endpointgroup_healthcheckprotocol only accepts valid values."""
    valid_protocols = ["HTTP", "HTTPS", "TCP"]
    if value in valid_protocols:
        assert endpointgroup_healthcheckprotocol(value) == value
    else:
        with pytest.raises(ValueError) as exc_info:
            endpointgroup_healthcheckprotocol(value)
        assert 'HealthCheckProtocol must be one of: "HTTP, HTTPS, TCP"' in str(exc_info.value)


@given(st.text())
def test_listener_clientaffinity_validator(value):
    """Test that listener_clientaffinity only accepts valid values."""
    valid_affinities = ["NONE", "SOURCE_IP"]
    if value in valid_affinities:
        assert listener_clientaffinity(value) == value
    else:
        with pytest.raises(ValueError) as exc_info:
            listener_clientaffinity(value)
        assert 'ClientAffinity must be one of: "NONE, SOURCE_IP"' in str(exc_info.value)


@given(st.text())
def test_listener_protocol_validator(value):
    """Test that listener_protocol only accepts valid values."""
    valid_protocols = ["TCP", "UDP"]
    if value in valid_protocols:
        assert listener_protocol(value) == value
    else:
        with pytest.raises(ValueError) as exc_info:
            listener_protocol(value)
        assert 'Protocol must be one of: "TCP, UDP"' in str(exc_info.value)


# Test 2: Round-trip property - to_dict() and from_dict() should be inverses
@given(
    name=st.text(min_size=1, max_size=100).filter(lambda x: x.isalnum()),
    enabled=st.booleans(),
    ip_type=st.sampled_from(["IPV4"])
)
def test_accelerator_round_trip(name, enabled, ip_type):
    """Test that Accelerator objects can round-trip through to_dict/from_dict."""
    # Create an Accelerator
    original = Accelerator(
        title="TestAccelerator",
        Name=name,
        Enabled=enabled,
        IpAddressType=ip_type
    )
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Extract properties
    props = dict_repr.get("Properties", {})
    
    # Create new object from dict
    reconstructed = Accelerator.from_dict("TestAccelerator", props)
    
    # Compare the objects
    assert original.Name == reconstructed.Name
    assert original.to_dict() == reconstructed.to_dict()


@given(
    from_port=st.integers(min_value=1, max_value=65535),
    to_port=st.integers(min_value=1, max_value=65535)
)
def test_portrange_round_trip(from_port, to_port):
    """Test that PortRange objects can round-trip through to_dict/from_dict."""
    # Create a PortRange
    original = PortRange(
        FromPort=from_port,
        ToPort=to_port
    )
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Create new object from dict
    reconstructed = PortRange.from_dict(None, dict_repr)
    
    # Compare
    assert original.FromPort == reconstructed.FromPort
    assert original.ToPort == reconstructed.ToPort
    assert original.to_dict() == reconstructed.to_dict()


# Test 3: PortRange invariant - test reasonable port ranges
@given(
    from_port=st.integers(min_value=1, max_value=65535),
    to_port=st.integers(min_value=1, max_value=65535)
)
def test_portrange_accepts_any_ports(from_port, to_port):
    """Test that PortRange accepts any valid port numbers."""
    # PortRange should accept any valid ports, even if FromPort > ToPort
    # This tests whether the code enforces the invariant
    port_range = PortRange(
        FromPort=from_port,
        ToPort=to_port
    )
    
    # Should successfully create and convert to dict
    dict_repr = port_range.to_dict()
    assert dict_repr["FromPort"] == from_port
    assert dict_repr["ToPort"] == to_port


# Test 4: Required property validation
@given(st.text(min_size=1, max_size=100).filter(lambda x: x.isalnum()))
def test_accelerator_requires_name(name):
    """Test that Accelerator enforces Name as required property."""
    # Create without Name should fail validation
    acc = Accelerator(title="TestAcc")
    
    # Calling to_dict() with validation should raise an error
    with pytest.raises(ValueError) as exc_info:
        acc.to_dict()
    assert "Resource Name required in type AWS::GlobalAccelerator::Accelerator" in str(exc_info.value)
    
    # With Name, it should work
    acc_with_name = Accelerator(title="TestAcc", Name=name)
    dict_repr = acc_with_name.to_dict()
    assert "Properties" in dict_repr
    assert dict_repr["Properties"]["Name"] == name


@given(
    st.text(min_size=1, max_size=100).filter(lambda x: x.isalnum()),
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100),
    st.sampled_from(["TCP", "UDP"])
)
def test_listener_required_properties(acc_arn, region, listener_arn, protocol):
    """Test that Listener enforces required properties."""
    # Test with missing required properties
    listener = Listener(title="TestListener")
    
    with pytest.raises(ValueError) as exc_info:
        listener.to_dict()
    # Should complain about missing required property
    assert "required in type AWS::GlobalAccelerator::Listener" in str(exc_info.value)
    
    # Test with all required properties
    listener_complete = Listener(
        title="TestListener",
        AcceleratorArn=acc_arn,
        Protocol=protocol,
        PortRanges=[PortRange(FromPort=80, ToPort=80)]
    )
    dict_repr = listener_complete.to_dict()
    assert dict_repr["Properties"]["AcceleratorArn"] == acc_arn
    assert dict_repr["Properties"]["Protocol"] == protocol


@given(
    endpoint_id=st.text(min_size=1, max_size=100),
    weight=st.integers(min_value=0, max_value=255)
)
def test_endpoint_configuration_required_property(endpoint_id, weight):
    """Test that EndpointConfiguration enforces EndpointId as required."""
    # Without EndpointId
    config = EndpointConfiguration()
    with pytest.raises(ValueError) as exc_info:
        config.to_dict()
    assert "Resource EndpointId required" in str(exc_info.value)
    
    # With EndpointId
    config_complete = EndpointConfiguration(EndpointId=endpoint_id, Weight=weight)
    dict_repr = config_complete.to_dict()
    assert dict_repr["EndpointId"] == endpoint_id
    if weight is not None:
        assert dict_repr["Weight"] == weight


# Test edge cases with special strings
@given(st.sampled_from(["", " ", "\t", "\n", "IPV4 ", " IPV4", "ipv4", "IPv4", "IP_V4", "IPV-4", "IPV4\n"]))
def test_ipaddresstype_edge_cases(value):
    """Test edge cases for IP address type validator."""
    if value == "IPV4":
        assert accelerator_ipaddresstype(value) == value
    else:
        with pytest.raises(ValueError):
            accelerator_ipaddresstype(value)


# Test that validators preserve exact input when valid
@given(st.sampled_from(["HTTP", "HTTPS", "TCP"]))
def test_healthcheck_protocol_preserves_exact_value(protocol):
    """Test that valid protocols are returned exactly as provided."""
    result = endpointgroup_healthcheckprotocol(protocol)
    assert result == protocol
    assert result is protocol  # Should be the same object


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])