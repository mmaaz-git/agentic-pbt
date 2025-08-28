#!/usr/bin/env python3
"""Property-based tests for troposphere.iotwireless module."""

import string
from hypothesis import assume, given, strategies as st, settings
import pytest
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import BaseAWSObject
from troposphere.validators import boolean, integer, positive_integer
import troposphere.iotwireless as iotwireless


# Test 1: Boolean validator accepts specific values
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
    st.text(min_size=1),
    st.integers(),
    st.floats(),
    st.none()
))
def test_boolean_validator(value):
    """Test that boolean validator only accepts documented values."""
    valid_true = [True, 1, "1", "true", "True"]
    valid_false = [False, 0, "0", "false", "False"]
    
    if value in valid_true:
        assert boolean(value) is True
    elif value in valid_false:
        assert boolean(value) is False
    else:
        with pytest.raises(ValueError):
            boolean(value)


# Test 2: Integer validator must accept valid integers and reject invalid ones
@given(st.one_of(
    st.integers(),
    st.text(alphabet=string.digits, min_size=1),
    st.floats(),
    st.text(min_size=1),
    st.none()
))
def test_integer_validator(value):
    """Test that integer validator accepts things convertible to int."""
    try:
        # Check if Python's int() would accept it
        int_val = int(value)
        # integer validator should accept it
        result = integer(value)
        assert result == value
    except (ValueError, TypeError):
        # If int() rejects it, integer validator should too
        with pytest.raises(ValueError):
            integer(value)


# Test 3: Positive integer validator
@given(st.integers(min_value=-10000, max_value=10000))
def test_positive_integer_validator(value):
    """Test that positive_integer validator only accepts non-negative integers."""
    if value >= 0:
        result = positive_integer(value)
        assert result == value
    else:
        with pytest.raises(ValueError):
            positive_integer(value)


# Test 4: Title validation for AWS objects (alphanumeric only)
@given(st.text(min_size=1, max_size=100))
def test_title_validation(title):
    """Test that AWS object titles must be alphanumeric."""
    # Create a simple test object
    try:
        obj = iotwireless.Destination(
            title=title,
            Expression="test",
            ExpressionType="RuleName", 
            Name="TestDest"
        )
        # If it succeeded, title should be alphanumeric
        assert title.isalnum(), f"Non-alphanumeric title {title!r} was accepted"
    except ValueError as e:
        # Should only fail if title is not alphanumeric
        if title and title.isalnum():
            raise AssertionError(f"Alphanumeric title {title!r} was rejected: {e}")


# Test 5: Round-trip property - dict to object to dict
@given(
    st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=50),
    st.text(min_size=1, max_size=100),
    st.sampled_from(["RuleName", "SnsTopic", "MqttTopic"])
)
def test_destination_round_trip(name, expression, expr_type):
    """Test round-trip property: creating from dict and converting back preserves data."""
    # Create original dict
    original_dict = {
        "Expression": expression,
        "ExpressionType": expr_type,
        "Name": name
    }
    
    # Create object from dict
    obj = iotwireless.Destination._from_dict(**original_dict)
    
    # Convert back to dict
    result_dict = obj.to_dict(validation=False)
    
    # Check Properties are preserved
    if "Properties" in result_dict:
        props = result_dict["Properties"]
    else:
        props = result_dict
        
    assert props["Expression"] == expression
    assert props["ExpressionType"] == expr_type
    assert props["Name"] == name


# Test 6: Required properties must be provided
def test_required_properties_validation():
    """Test that required properties must be provided when validation is enabled."""
    # Create object without required properties
    obj = iotwireless.Destination("TestDest")
    
    # Should fail validation because Expression and ExpressionType are required
    with pytest.raises(ValueError):
        obj.to_dict(validation=True)


# Test 7: Optional properties can be omitted
@given(st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=50))
def test_optional_properties(name):
    """Test that optional properties can be omitted without validation errors."""
    obj = iotwireless.Destination(
        title="TestDest",
        Expression="test",
        ExpressionType="RuleName",
        Name=name
        # Description and RoleArn are optional and omitted
    )
    
    # Should not raise any validation errors
    result = obj.to_dict(validation=True)
    assert "Type" in result
    assert result["Type"] == "AWS::IoTWireless::Destination"


# Test 8: Integer properties in LoRaWAN classes
@given(st.integers())
def test_lorawan_integer_properties(value):
    """Test that integer properties in LoRaWAN classes validate correctly."""
    profile = iotwireless.LoRaWANDeviceProfile()
    
    # Try setting an integer property
    try:
        profile.ClassBTimeout = value
        # If it succeeded, the value should be stored
        assert profile.ClassBTimeout == value
    except (ValueError, TypeError):
        # Some values might be rejected by additional validation
        pass


# Test 9: Boolean properties in LoRaWAN classes  
@given(st.one_of(
    st.booleans(),
    st.sampled_from([0, 1, "true", "false", "True", "False"])
))
def test_lorawan_boolean_properties(value):
    """Test that boolean properties validate correctly."""
    profile = iotwireless.LoRaWANDeviceProfile()
    
    valid_values = [True, False, 0, 1, "true", "false", "True", "False", "0", "1"]
    
    if value in valid_values:
        profile.Supports32BitFCnt = value
        # Value should be stored (possibly converted)
        assert hasattr(profile, 'properties')
    else:
        # Invalid boolean values should be rejected
        with pytest.raises((ValueError, TypeError)):
            profile.Supports32BitFCnt = value


# Test 10: Nested property objects
@given(
    st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=50),
    st.sampled_from(["US915", "EU868", "AU915", "AS923-1"])
)
def test_nested_property_objects(task_name, rf_region):
    """Test that nested property objects work correctly."""
    # Create a nested LoRaWAN property
    lorawan_config = iotwireless.FuotaTaskLoRaWAN(RfRegion=rf_region)
    
    # Create main object with nested property
    task = iotwireless.FuotaTask(
        title="TestTask",
        FirmwareUpdateImage="s3://bucket/firmware.bin",
        FirmwareUpdateRole="arn:aws:iam::123456789012:role/TestRole",
        LoRaWAN=lorawan_config,
        Name=task_name
    )
    
    # Convert to dict and verify nested structure
    result = task.to_dict(validation=False)
    props = result.get("Properties", result)
    
    assert "LoRaWAN" in props
    assert props["LoRaWAN"]["RfRegion"] == rf_region
    assert props["Name"] == task_name


# Test 11: List properties
@given(st.lists(st.integers(min_value=0, max_value=1000000), min_size=0, max_size=10))
def test_list_properties(freq_list):
    """Test that list properties handle lists correctly."""
    profile = iotwireless.LoRaWANDeviceProfile()
    profile.FactoryPresetFreqsList = freq_list
    
    # Should store the list
    assert profile.FactoryPresetFreqsList == freq_list
    
    # Test in dict conversion
    obj = iotwireless.DeviceProfile(
        title="TestProfile",
        LoRaWAN=profile
    )
    result = obj.to_dict(validation=False)
    props = result.get("Properties", result)
    
    if freq_list:  # Only check if list is non-empty
        assert props["LoRaWAN"]["FactoryPresetFreqsList"] == freq_list


# Test 12: Property type checking 
@given(
    st.one_of(
        st.text(),
        st.integers(),
        st.floats(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_property_type_checking(value):
    """Test that properties validate their expected types."""
    obj = iotwireless.Destination(title="Test")
    
    # Expression expects a string
    if isinstance(value, str):
        obj.Expression = value
        assert obj.Expression == value
    else:
        with pytest.raises(TypeError):
            obj.Expression = value


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])