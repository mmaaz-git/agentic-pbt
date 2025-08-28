#!/usr/bin/env python3
"""
Property-based tests for troposphere.iotfleetwise module.
Testing fundamental properties that should always hold.
"""

import sys
import json
from typing import Any, Dict, List, Optional
import hypothesis.strategies as st
from hypothesis import given, assume, settings, example
import pytest

# Add the site-packages to path to import troposphere
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

import troposphere.iotfleetwise as iotfleetwise
from troposphere import Tags


# Strategy for generating valid property values based on type
def value_for_type(prop_type):
    """Generate valid values for a given property type."""
    if prop_type == str:
        return st.text(min_size=1, max_size=100)
    elif prop_type == int or prop_type.__name__ == "integer":
        return st.integers(min_value=0, max_value=1000000)
    elif prop_type == float or prop_type.__name__ == "double":
        return st.floats(min_value=0.0, max_value=1000000.0, allow_nan=False, allow_infinity=False)
    elif prop_type == bool:
        return st.booleans()
    elif prop_type == dict:
        return st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50), max_size=5)
    elif isinstance(prop_type, list):
        # It's a list of something
        if len(prop_type) > 0:
            inner_type = prop_type[0]
            if inner_type == str:
                return st.lists(st.text(min_size=1, max_size=50), max_size=5)
            else:
                # For AWS objects in lists, we'd need recursive strategies
                return st.just([])
    elif hasattr(prop_type, '__bases__') and any('AWSProperty' in str(base) for base in prop_type.__bases__):
        # It's an AWS property type - for now return None to skip
        return st.none()
    else:
        return st.none()


def generate_valid_object_data(cls):
    """Generate valid data for creating an object of the given class."""
    strategies = {}
    
    for prop_name, (prop_type, required) in cls.props.items():
        value_strategy = value_for_type(prop_type)
        
        if required:
            strategies[prop_name] = value_strategy
        else:
            # Optional properties - sometimes include, sometimes don't
            strategies[prop_name] = st.one_of(st.none(), value_strategy)
    
    return st.fixed_dictionaries(strategies)


# Test 1: Round-trip property - from_dict(to_dict(x)) should equal x
@given(
    name=st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    signal_catalog_arn=st.text(min_size=20, max_size=100),
    target_arn=st.text(min_size=20, max_size=100),
    period_ms=st.floats(min_value=1.0, max_value=1000000.0, allow_nan=False, allow_infinity=False),
)
def test_campaign_round_trip(name, signal_catalog_arn, target_arn, period_ms):
    """Test that Campaign objects survive to_dict/from_dict round-trip."""
    # Create a Campaign with minimal required properties
    time_based = iotfleetwise.TimeBasedCollectionScheme(PeriodMs=period_ms)
    collection_scheme = iotfleetwise.CollectionScheme(TimeBasedCollectionScheme=time_based)
    
    original = iotfleetwise.Campaign(
        title="TestCampaign",
        Name=name,
        SignalCatalogArn=signal_catalog_arn,
        TargetArn=target_arn,
        CollectionScheme=collection_scheme
    )
    
    # Convert to dict and back
    dict_repr = original.to_dict(validation=False)
    
    # Extract the Properties part for from_dict
    if "Properties" in dict_repr:
        props = dict_repr["Properties"]
        reconstructed = iotfleetwise.Campaign.from_dict("TestCampaign", props)
        
        # Check equality
        assert original == reconstructed


# Test 2: Required property validation
@given(
    name=st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
)
def test_campaign_required_properties(name):
    """Test that Campaign raises error when required properties are missing."""
    # Try to create a Campaign without all required properties
    with pytest.raises((ValueError, TypeError)):
        campaign = iotfleetwise.Campaign(
            title="TestCampaign",
            Name=name,
            # Missing: SignalCatalogArn, TargetArn, CollectionScheme
        )
        # Force validation
        campaign.to_dict(validation=True)


# Test 3: Type validation for properties
@given(
    invalid_value=st.one_of(
        st.integers(),
        st.floats(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_fleet_type_validation(invalid_value):
    """Test that Fleet validates property types correctly."""
    fleet = iotfleetwise.Fleet(title="TestFleet")
    
    # Id should be a string, try setting it to invalid types
    if not isinstance(invalid_value, str):
        with pytest.raises((TypeError, AttributeError)):
            fleet.Id = invalid_value


# Test 4: SignalCatalog node properties
@given(
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    fully_qualified_name=st.text(min_size=1, max_size=100),
    data_type=st.sampled_from(["BOOLEAN", "INT32", "INT64", "FLOAT", "DOUBLE", "STRING"]),
    min_val=st.floats(min_value=-1000000, max_value=0, allow_nan=False, allow_infinity=False),
    max_val=st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False),
)
def test_sensor_property_consistency(name, fully_qualified_name, data_type, min_val, max_val):
    """Test that Sensor objects maintain property consistency."""
    sensor = iotfleetwise.Sensor(
        FullyQualifiedName=fully_qualified_name,
        DataType=data_type
    )
    
    # Set min and max
    sensor.Min = min_val
    sensor.Max = max_val
    
    # Properties should be accessible
    assert sensor.FullyQualifiedName == fully_qualified_name
    assert sensor.DataType == data_type
    
    # Convert to dict should preserve values
    sensor_dict = sensor.to_dict(validation=False)
    assert sensor_dict["FullyQualifiedName"] == fully_qualified_name
    assert sensor_dict["DataType"] == data_type


# Test 5: StateTemplate round-trip
@given(
    name=st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    signal_catalog_arn=st.text(min_size=20, max_size=100),
    state_props=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5),
    description=st.text(max_size=200),
)
def test_state_template_round_trip(name, signal_catalog_arn, state_props, description):
    """Test StateTemplate to_dict/from_dict round-trip."""
    original = iotfleetwise.StateTemplate(
        title="TestStateTemplate",
        Name=name,
        SignalCatalogArn=signal_catalog_arn,
        StateTemplateProperties=state_props,
        Description=description if description else None
    )
    
    dict_repr = original.to_dict(validation=False)
    
    if "Properties" in dict_repr:
        props = dict_repr["Properties"]
        reconstructed = iotfleetwise.StateTemplate.from_dict("TestStateTemplate", props)
        
        # The objects should be equal
        assert original == reconstructed


# Test 6: Vehicle attribute handling
@given(
    vehicle_name=st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    decoder_arn=st.text(min_size=20, max_size=100),
    model_arn=st.text(min_size=20, max_size=100),
    attributes=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.text(min_size=1, max_size=50),
        max_size=5
    )
)
def test_vehicle_attributes(vehicle_name, decoder_arn, model_arn, attributes):
    """Test that Vehicle handles Attributes property correctly."""
    vehicle = iotfleetwise.Vehicle(
        title="TestVehicle",
        Name=vehicle_name,
        DecoderManifestArn=decoder_arn,
        ModelManifestArn=model_arn,
        Attributes=attributes
    )
    
    # Check that attributes are set correctly
    assert vehicle.Name == vehicle_name
    assert vehicle.Attributes == attributes
    
    # Convert to dict and verify attributes are preserved
    vehicle_dict = vehicle.to_dict(validation=False)
    if attributes:
        assert vehicle_dict["Properties"]["Attributes"] == attributes


# Test 7: DecoderManifest network interfaces
@given(
    interface_id=st.text(min_size=1, max_size=50),
    interface_name=st.text(min_size=1, max_size=50),
    interface_type=st.sampled_from(["CAN_INTERFACE", "OBD_INTERFACE", "CUSTOM_DECODING_INTERFACE"])
)
def test_decoder_manifest_network_interface(interface_id, interface_name, interface_type):
    """Test DecoderManifest handles network interfaces correctly."""
    # Create appropriate interface based on type
    if interface_type == "CAN_INTERFACE":
        interface = iotfleetwise.CanInterface(Name=interface_name)
        network_interface = iotfleetwise.NetworkInterfacesItems(
            InterfaceId=interface_id,
            Type=interface_type,
            CanInterface=interface
        )
    elif interface_type == "OBD_INTERFACE":
        interface = iotfleetwise.ObdInterface(
            Name=interface_name,
            RequestMessageId="0x7DF"
        )
        network_interface = iotfleetwise.NetworkInterfacesItems(
            InterfaceId=interface_id,
            Type=interface_type,
            ObdInterface=interface
        )
    else:
        interface = iotfleetwise.CustomDecodingInterface(Name=interface_name)
        network_interface = iotfleetwise.NetworkInterfacesItems(
            InterfaceId=interface_id,
            Type=interface_type,
            CustomDecodingInterface=interface
        )
    
    # Create DecoderManifest
    decoder = iotfleetwise.DecoderManifest(
        title="TestDecoder",
        Name="TestDecoderManifest",
        ModelManifestArn="arn:aws:iotfleetwise:us-east-1:123456789012:model-manifest/test",
        NetworkInterfaces=[network_interface]
    )
    
    # Verify it was created successfully
    assert decoder.Name == "TestDecoderManifest"
    assert len(decoder.NetworkInterfaces) == 1


if __name__ == "__main__":
    # Run the tests with pytest
    pytest.main([__file__, "-v"])