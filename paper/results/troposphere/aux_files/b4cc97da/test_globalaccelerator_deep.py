#!/usr/bin/env python3
"""Deep property-based tests for troposphere.globalaccelerator module - looking for edge cases."""

import sys
import json
from hypothesis import given, strategies as st, assume, settings, note
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
from troposphere import Tags


# Test complex object creation with edge case values
@given(
    name=st.text(min_size=1).filter(lambda x: x.isalnum()),
    enabled=st.booleans(),
    ips=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    tags=st.dictionaries(
        st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
        st.text(min_size=0, max_size=200),
        max_size=10
    )
)
@settings(max_examples=1000)
def test_accelerator_with_complex_properties(name, enabled, ips, tags):
    """Test Accelerator with various property combinations."""
    # Create accelerator with all optional properties
    acc = Accelerator(
        title="TestAcc",
        Name=name,
        Enabled=enabled,
        IpAddresses=ips,
        IpAddressType="IPV4",
        Tags=Tags(tags) if tags else None
    )
    
    # Should be able to convert to dict
    dict_repr = acc.to_dict()
    assert dict_repr["Properties"]["Name"] == name
    
    # Try round-trip
    props = dict_repr.get("Properties", {})
    reconstructed = Accelerator.from_dict("TestAcc", props)
    assert reconstructed.Name == name
    
    # Check that all properties are preserved
    if enabled is not None:
        assert reconstructed.to_dict()["Properties"].get("Enabled") == enabled
    if ips:
        assert reconstructed.to_dict()["Properties"].get("IpAddresses") == ips


# Test EndpointGroup with all properties
@given(
    region=st.text(min_size=1, max_size=20).filter(lambda x: x.replace("-", "").isalnum()),
    listener_arn=st.text(min_size=20, max_size=100),
    health_interval=st.integers(min_value=10, max_value=30),
    health_path=st.text(min_size=0, max_size=255),
    health_port=st.integers(min_value=1, max_value=65535),
    health_protocol=st.sampled_from(["HTTP", "HTTPS", "TCP"]),
    threshold=st.integers(min_value=1, max_value=10),
    traffic_dial=st.floats(min_value=0.0, max_value=100.0, allow_nan=False)
)
def test_endpointgroup_all_properties(region, listener_arn, health_interval, 
                                     health_path, health_port, health_protocol,
                                     threshold, traffic_dial):
    """Test EndpointGroup with all optional properties."""
    eg = EndpointGroup(
        title="TestEG",
        EndpointGroupRegion=region,
        ListenerArn=listener_arn,
        HealthCheckIntervalSeconds=health_interval,
        HealthCheckPath=health_path,
        HealthCheckPort=health_port,
        HealthCheckProtocol=health_protocol,
        ThresholdCount=threshold,
        TrafficDialPercentage=traffic_dial
    )
    
    dict_repr = eg.to_dict()
    props = dict_repr["Properties"]
    
    # Verify all properties are preserved
    assert props["EndpointGroupRegion"] == region
    assert props["ListenerArn"] == listener_arn
    assert props.get("HealthCheckIntervalSeconds") == health_interval
    assert props.get("TrafficDialPercentage") == traffic_dial
    
    # Round-trip test
    reconstructed = EndpointGroup.from_dict("TestEG", props)
    assert reconstructed.to_dict() == dict_repr


# Test PortOverride edge cases
@given(
    endpoint_port=st.integers(min_value=-100, max_value=100000),
    listener_port=st.integers(min_value=-100, max_value=100000)
)
def test_portoverride_accepts_invalid_ports(endpoint_port, listener_port):
    """Test if PortOverride validates port numbers."""
    # PortOverride might not validate port ranges
    try:
        po = PortOverride(
            EndpointPort=endpoint_port,
            ListenerPort=listener_port
        )
        dict_repr = po.to_dict()
        # If it accepts the values, they should be preserved
        assert dict_repr["EndpointPort"] == endpoint_port
        assert dict_repr["ListenerPort"] == listener_port
    except (ValueError, TypeError) as e:
        # If it does validate, that's also fine
        note(f"PortOverride validation caught invalid port: {e}")
        pass


# Test CrossAccountAttachment with nested Resources
@given(
    name=st.text(min_size=1, max_size=100).filter(lambda x: x.isalnum()),
    principals=st.lists(st.text(min_size=1, max_size=100), max_size=5),
    resources=st.lists(
        st.fixed_dictionaries({
            "Cidr": st.text(min_size=1, max_size=20),
            "EndpointId": st.text(min_size=1, max_size=100),
            "Region": st.text(min_size=1, max_size=20)
        }),
        max_size=5
    )
)
def test_crossaccount_attachment_nested(name, principals, resources):
    """Test CrossAccountAttachment with nested Resource objects."""
    # Create Resource objects
    resource_objs = [Resource(**r) for r in resources]
    
    attachment = CrossAccountAttachment(
        title="TestAttachment",
        Name=name,
        Principals=principals,
        Resources=resource_objs
    )
    
    dict_repr = attachment.to_dict()
    props = dict_repr["Properties"]
    
    assert props["Name"] == name
    if principals:
        assert props.get("Principals") == principals
    if resources:
        assert len(props.get("Resources", [])) == len(resources)
        # Check that nested resources are properly converted
        for i, res_dict in enumerate(props.get("Resources", [])):
            assert res_dict["EndpointId"] == resources[i]["EndpointId"]


# Test type coercion and validation
@given(
    weight_value=st.one_of(
        st.integers(min_value=-1000, max_value=1000),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.none()
    )
)
def test_endpoint_configuration_weight_types(weight_value):
    """Test how EndpointConfiguration handles different types for Weight."""
    endpoint_id = "test-endpoint"
    
    try:
        config = EndpointConfiguration(
            EndpointId=endpoint_id,
            Weight=weight_value
        )
        dict_repr = config.to_dict()
        
        # If it accepts the value, check what it becomes
        if weight_value is not None:
            stored_weight = dict_repr.get("Weight")
            note(f"Weight {weight_value} (type {type(weight_value)}) stored as {stored_weight} (type {type(stored_weight)})")
            
            # If it's supposed to be an integer, check if type conversion happens
            if isinstance(weight_value, (int, float)) and not isinstance(weight_value, bool):
                assert isinstance(stored_weight, (int, float))
    except (TypeError, ValueError) as e:
        # Type validation is working
        note(f"EndpointConfiguration rejected {weight_value}: {e}")
        if isinstance(weight_value, str):
            # Strings should probably be rejected for integer fields
            pass
        elif isinstance(weight_value, float):
            # Floats might be rejected for integer fields
            pass


# Test empty/minimal objects
@given(st.just(None))
def test_minimal_objects(dummy):
    """Test creating objects with only required fields."""
    # Accelerator with just Name
    acc = Accelerator(title="MinAcc", Name="TestName")
    assert acc.to_dict()["Properties"]["Name"] == "TestName"
    
    # Listener with just required fields
    listener = Listener(
        title="MinListener",
        AcceleratorArn="arn:aws:test",
        Protocol="TCP",
        PortRanges=[PortRange(FromPort=80, ToPort=80)]
    )
    assert listener.to_dict()["Properties"]["Protocol"] == "TCP"
    
    # EndpointGroup with just required fields
    eg = EndpointGroup(
        title="MinEG",
        EndpointGroupRegion="us-east-1",
        ListenerArn="arn:aws:listener"
    )
    assert eg.to_dict()["Properties"]["EndpointGroupRegion"] == "us-east-1"


# Test special characters in strings
@given(
    name=st.text(min_size=1).filter(lambda x: any(c.isalnum() for c in x)),
    special_string=st.sampled_from([
        "test\x00null",  # null byte
        "test\ttab",     # tab
        "test\nnewline", # newline
        "test\rcarriage",# carriage return
        "test\"quote",   # double quote
        "test'quote",    # single quote
        "test\\escape",  # backslash
        "test{brace",    # brace
        "test}brace",    # brace
        "test[bracket",  # bracket
        "test]bracket",  # bracket
    ])
)
def test_special_characters_in_properties(name, special_string):
    """Test how special characters are handled in string properties."""
    try:
        acc = Accelerator(
            title="TestAcc",
            Name=name,
            IpAddresses=[special_string]
        )
        dict_repr = acc.to_dict()
        
        # Special characters should be preserved in the output
        assert dict_repr["Properties"]["IpAddresses"][0] == special_string
        
        # Test JSON serialization
        json_str = json.dumps(dict_repr)
        reloaded = json.loads(json_str)
        assert reloaded["Properties"]["IpAddresses"][0] == special_string
        
    except Exception as e:
        note(f"Failed with special string '{special_string}': {e}")
        raise


# Test very large numbers for integer fields
@given(
    big_int=st.one_of(
        st.integers(min_value=2**31, max_value=2**63),  # Large positive
        st.integers(min_value=-2**63, max_value=-2**31), # Large negative
        st.just(2**31 - 1),  # Max 32-bit signed
        st.just(-2**31),     # Min 32-bit signed
        st.just(2**32 - 1),  # Max 32-bit unsigned
    )
)
def test_large_integers(big_int):
    """Test how large integers are handled."""
    try:
        po = PortOverride(
            EndpointPort=big_int,
            ListenerPort=80
        )
        dict_repr = po.to_dict()
        assert dict_repr["EndpointPort"] == big_int
        
        # Can it round-trip?
        reconstructed = PortOverride.from_dict(None, dict_repr)
        assert reconstructed.EndpointPort == big_int
        
    except (ValueError, TypeError, OverflowError) as e:
        # If it validates the range, that's good
        note(f"PortOverride rejected large integer {big_int}: {e}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])