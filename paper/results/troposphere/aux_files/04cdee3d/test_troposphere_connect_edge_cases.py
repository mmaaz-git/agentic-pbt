"""More comprehensive property-based tests for troposphere.connect module - edge cases."""

import sys
import os

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import pytest
import json

# Import the module under test
from troposphere import connect
from troposphere import validators
from troposphere import AWSObject, AWSProperty, BaseAWSObject


# Test special integer edge cases
@given(st.sampled_from([
    "1", "01", "001", "+1", "-1",
    "1.0", "1.5", "1e0", "1e1",
    " 1 ", "\t1\n", 
    "", " ", "NaN", "inf", "-inf",
    "0x10", "0o10", "0b10",
    True, False,
    1.0, 1.5, float('inf'), float('-inf'), float('nan')
]))
def test_integer_validator_edge_cases(value):
    """Test integer validator with edge cases."""
    # Check what Python's int() accepts vs what the validator accepts
    
    try:
        expected = int(value)
        # If int() succeeds, validator should too
        result = validators.integer(value)
        assert result == value  # validator returns original value
    except (ValueError, TypeError):
        # If int() fails, validator should fail
        with pytest.raises(ValueError):
            validators.integer(value)


# Test special double edge cases
@given(st.sampled_from([
    "1.0", "1.5", "-1.5", "+1.5",
    "1e0", "1e10", "1e-10", "1E10",
    "inf", "-inf", "Infinity", "-Infinity",
    "nan", "NaN", "NAN",
    "", " ", "  1.5  ",
    True, False,
    1, 0, -1
]))
def test_double_validator_edge_cases(value):
    """Test double validator with edge cases."""
    
    try:
        expected = float(value)
        # If float() succeeds, validator should too
        result = validators.double(value)
        assert result == value  # validator returns original value
    except (ValueError, TypeError):
        # If float() fails, validator should fail
        with pytest.raises(ValueError):
            validators.double(value)


# Test boolean with numeric edge cases
@given(st.sampled_from([
    "1", "0", 1, 0,
    1.0, 0.0,
    "01", "00",
    " true ", " false ",
    "TRUE", "FALSE",
    "True ", " False",
    2, -1, "2", "-1",
    "", None,
    [], {}, 
    [True], [False],
    {"true": True}
]))
def test_boolean_validator_numeric_edge_cases(value):
    """Test boolean validator with numeric and string edge cases."""
    
    true_values = [True, 1, "1", "true", "True"]
    false_values = [False, 0, "0", "false", "False"]
    
    if value in true_values:
        assert validators.boolean(value) is True
    elif value in false_values:
        assert validators.boolean(value) is False
    else:
        with pytest.raises(ValueError):
            validators.boolean(value)


# Test network port with strings and floats
@given(st.one_of(
    st.text(),
    st.floats(),
    st.sampled_from(["-1", "0", "65535", "65536", "1.5", "80.0"])
))
def test_network_port_string_inputs(value):
    """Test network_port validator with string and float inputs."""
    
    try:
        int_val = int(value)
        if -1 <= int_val <= 65535:
            result = validators.network_port(value)
            assert result == value
        else:
            with pytest.raises(ValueError):
                validators.network_port(value)
    except (ValueError, TypeError):
        with pytest.raises(ValueError):
            validators.network_port(value)


# Test creating objects with invalid property types
@given(
    hours=st.one_of(st.text(), st.floats(), st.none(), st.lists(st.integers())),
    minutes=st.one_of(st.text(), st.floats(), st.none(), st.lists(st.integers()))
)
def test_hours_of_operation_invalid_types(hours, minutes):
    """Test HoursOfOperationTimeSlice with invalid types."""
    
    # This tests whether the type validation works correctly
    try:
        # Try to create the object
        time_slice = connect.HoursOfOperationTimeSlice(
            Hours=hours,
            Minutes=minutes
        )
        
        # If it succeeds, both should be convertible to int
        int(hours)
        int(minutes)
        
        # And to_dict should work
        result = time_slice.to_dict()
        assert "Hours" in result
        assert "Minutes" in result
        
    except (ValueError, TypeError):
        # Creation or validation should fail for non-integer types
        pass


# Test FieldValue union type edge cases
@given(
    boolean_val=st.booleans(),
    double_val=st.floats(allow_nan=False, allow_infinity=False),
    empty_val=st.just({}),
    string_val=st.text()
)
def test_field_value_union_types(boolean_val, double_val, empty_val, string_val):
    """Test FieldValue with its union of types."""
    
    # FieldValue can have BooleanValue, DoubleValue, EmptyValue, or StringValue
    # Only one should be set at a time based on the class definition
    
    # Test with boolean
    fv1 = connect.FieldValue(BooleanValue=boolean_val)
    result1 = fv1.to_dict()
    assert result1["BooleanValue"] == boolean_val
    
    # Test with double
    fv2 = connect.FieldValue(DoubleValue=double_val)
    result2 = fv2.to_dict()
    assert result2["DoubleValue"] == double_val
    
    # Test with empty
    fv3 = connect.FieldValue(EmptyValue=empty_val)
    result3 = fv3.to_dict()
    assert result3["EmptyValue"] == empty_val
    
    # Test with string
    fv4 = connect.FieldValue(StringValue=string_val)
    result4 = fv4.to_dict()
    assert result4["StringValue"] == string_val


# Test title validation for AWS objects
@given(st.text())
def test_aws_object_title_validation(title):
    """Test that AWS object titles must be alphanumeric."""
    
    import re
    
    # According to the code, titles must match ^[a-zA-Z0-9]+$
    valid_names = re.compile(r"^[a-zA-Z0-9]+$")
    
    if title and valid_names.match(title):
        # Should succeed
        agent = connect.AgentStatus(
            title,
            InstanceArn="arn:aws:connect:us-east-1:123456789012:instance/test",
            Name="TestName",
            State="ENABLED"
        )
        assert agent.title == title
    elif title:  # Non-empty but invalid
        # Should raise ValueError
        with pytest.raises(ValueError, match="not alphanumeric"):
            connect.AgentStatus(
                title,
                InstanceArn="arn:aws:connect:us-east-1:123456789012:instance/test",
                Name="TestName", 
                State="ENABLED"
            )
    else:  # Empty title - allowed
        agent = connect.AgentStatus(
            title,
            InstanceArn="arn:aws:connect:us-east-1:123456789012:instance/test",
            Name="TestName",
            State="ENABLED"
        )
        assert agent.title == title


# Test creating objects without required properties  
def test_missing_required_properties():
    """Test that objects cannot be created without required properties."""
    
    # AgentStatus requires InstanceArn, Name, and State
    
    # Missing InstanceArn
    with pytest.raises(TypeError):
        connect.AgentStatus(
            "TestAgent",
            Name="TestName",
            State="ENABLED"
        )
    
    # Missing Name
    with pytest.raises(TypeError):
        connect.AgentStatus(
            "TestAgent",
            InstanceArn="arn:aws:connect:us-east-1:123456789012:instance/test",
            State="ENABLED"
        )
    
    # Missing State
    with pytest.raises(TypeError):
        connect.AgentStatus(
            "TestAgent",
            InstanceArn="arn:aws:connect:us-east-1:123456789012:instance/test",
            Name="TestName"
        )


# Test property type enforcement
@given(
    display_order=st.one_of(st.text(), st.floats(), st.lists(st.integers())),
    reset_order=st.one_of(st.integers(), st.text(), st.lists(st.booleans()))
)
def test_property_type_enforcement(display_order, reset_order):
    """Test that properties enforce their declared types."""
    
    # DisplayOrder should be integer
    # ResetOrderNumber should be boolean
    
    try:
        agent = connect.AgentStatus(
            "TestAgent",
            InstanceArn="arn:aws:connect:us-east-1:123456789012:instance/test",
            Name="TestName",
            State="ENABLED",
            DisplayOrder=display_order,
            ResetOrderNumber=reset_order
        )
        
        # If creation succeeded, check type conversion worked
        result = agent.to_dict()
        
        # DisplayOrder uses integer validator
        int(display_order)  # Should not raise
        
        # ResetOrderNumber uses boolean validator
        assert reset_order in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]
        
    except (ValueError, TypeError):
        # Type validation should have failed
        pass


# Test JSON serialization edge cases
@given(
    name=st.text(min_size=1),
    state=st.sampled_from(["ENABLED", "DISABLED", "SOFT_DELETE"])
)
def test_json_serialization(name, state):
    """Test JSON serialization of objects."""
    
    # Filter out invalid titles
    import re
    valid_names = re.compile(r"^[a-zA-Z0-9]+$")
    assume(valid_names.match("ValidTitle123"))
    
    agent = connect.AgentStatus(
        "ValidTitle123",
        InstanceArn="arn:aws:connect:us-east-1:123456789012:instance/test",
        Name=name,
        State=state
    )
    
    # Convert to JSON
    json_str = agent.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    
    # Should have expected structure
    assert parsed["Type"] == "AWS::Connect::AgentStatus"
    assert parsed["Properties"]["Name"] == name
    assert parsed["Properties"]["State"] == state


# Test from_dict reconstruction
@given(
    hours=st.integers(min_value=0, max_value=23),
    minutes=st.integers(min_value=0, max_value=59)
)
def test_from_dict_reconstruction(hours, minutes):
    """Test that _from_dict correctly reconstructs objects."""
    
    # Create original
    original = connect.HoursOfOperationTimeSlice(
        Hours=hours,
        Minutes=minutes
    )
    
    # Get dict representation
    dict_repr = original.to_dict()
    
    # Reconstruct
    reconstructed = connect.HoursOfOperationTimeSlice._from_dict(**dict_repr)
    
    # Compare dict representations
    assert reconstructed.to_dict() == dict_repr
    
    # Properties should match
    assert reconstructed.properties["Hours"] == hours
    assert reconstructed.properties["Minutes"] == minutes


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short", "-x"])