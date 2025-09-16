"""Property-based tests for troposphere.connect module."""

import sys
import os

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the module under test
from troposphere import connect
from troposphere import validators
from troposphere import AWSObject, AWSProperty


# Test 1: Boolean validator properties
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"]),
    st.text(),
    st.integers(),
    st.floats(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
def test_boolean_validator(value):
    """Test the boolean validator function."""
    # Property: boolean() should return True for truthy values, False for falsy values
    # and raise ValueError for invalid values
    
    true_values = [True, 1, "1", "true", "True"]
    false_values = [False, 0, "0", "false", "False"]
    
    if value in true_values:
        assert validators.boolean(value) is True
    elif value in false_values:
        assert validators.boolean(value) is False
    else:
        with pytest.raises(ValueError):
            validators.boolean(value)


# Test 2: Integer validator properties
@given(st.one_of(
    st.integers(),
    st.text(),
    st.floats(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
def test_integer_validator(value):
    """Test the integer validator function."""
    # Property: integer() should accept values convertible to int, reject others
    
    try:
        int(value)
        result = validators.integer(value)
        assert result == value
    except (ValueError, TypeError):
        with pytest.raises(ValueError):
            validators.integer(value)


# Test 3: Double validator properties
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(),
    st.none(),
    st.lists(st.floats()),
    st.dictionaries(st.text(), st.text())
))
def test_double_validator(value):
    """Test the double validator function."""
    # Property: double() should accept values convertible to float, reject others
    
    try:
        float(value)
        result = validators.double(value)
        assert result == value
    except (ValueError, TypeError):
        with pytest.raises(ValueError):
            validators.double(value)


# Test 4: Network port validator
@given(st.integers())
def test_network_port_validator(value):
    """Test the network_port validator."""
    # Property: network_port should only accept values from -1 to 65535
    
    if -1 <= value <= 65535:
        result = validators.network_port(value)
        assert result == value
    else:
        with pytest.raises(ValueError):
            validators.network_port(value)


# Test 5: S3 bucket name validator
@given(st.text(min_size=1))
def test_s3_bucket_name_validator(name):
    """Test the s3_bucket_name validator."""
    # Property: S3 bucket names have specific requirements
    
    import re
    
    # Check for consecutive periods
    has_consecutive_periods = ".." in name
    
    # Check if it's an IP address
    ip_re = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    is_ip = bool(ip_re.match(name))
    
    # Check if it matches the valid pattern
    s3_bucket_name_re = re.compile(r"^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$")
    matches_pattern = bool(s3_bucket_name_re.match(name))
    
    if has_consecutive_periods or is_ip or not matches_pattern:
        with pytest.raises(ValueError):
            validators.s3_bucket_name(name)
    else:
        result = validators.s3_bucket_name(name)
        assert result == name


# Test 6: HoursOfOperationTimeSlice properties
@given(
    hours=st.integers(),
    minutes=st.integers()
)
def test_hours_of_operation_time_slice(hours, minutes):
    """Test HoursOfOperationTimeSlice creation and validation."""
    # Property: HoursOfOperationTimeSlice should validate hours and minutes as integers
    
    try:
        time_slice = connect.HoursOfOperationTimeSlice(
            Hours=hours,
            Minutes=minutes
        )
        # If creation succeeds, to_dict should work
        result = time_slice.to_dict()
        assert "Hours" in result
        assert "Minutes" in result
    except (ValueError, TypeError):
        # Some values might not be valid
        pass


# Test 7: AgentStatus required properties
@given(
    description=st.text(),
    display_order=st.integers(),
    instance_arn=st.text(min_size=1),
    name=st.text(min_size=1),
    reset_order=st.booleans(),
    state=st.text(min_size=1),
    type_str=st.text()
)
def test_agent_status_creation(description, display_order, instance_arn, 
                               name, reset_order, state, type_str):
    """Test AgentStatus creation with various property values."""
    # Property: AgentStatus requires InstanceArn, Name, and State
    
    # Create with all required properties
    agent = connect.AgentStatus(
        "TestAgent",
        InstanceArn=instance_arn,
        Name=name,
        State=state
    )
    
    # Should be able to convert to dict
    result = agent.to_dict()
    assert result["Type"] == "AWS::Connect::AgentStatus"
    assert result["Properties"]["InstanceArn"] == instance_arn
    assert result["Properties"]["Name"] == name
    assert result["Properties"]["State"] == state
    
    # Test optional properties
    agent2 = connect.AgentStatus(
        "TestAgent2",
        InstanceArn=instance_arn,
        Name=name,
        State=state,
        Description=description,
        DisplayOrder=display_order,
        ResetOrderNumber=reset_order,
        Type=type_str
    )
    
    result2 = agent2.to_dict()
    if description:
        assert result2["Properties"]["Description"] == description
    assert result2["Properties"]["DisplayOrder"] == display_order
    assert result2["Properties"]["ResetOrderNumber"] == reset_order
    if type_str:
        assert result2["Properties"]["Type"] == type_str


# Test 8: Round-trip property for simple objects
@given(
    hours=st.integers(min_value=0, max_value=23),
    minutes=st.integers(min_value=0, max_value=59)
)
def test_time_slice_round_trip(hours, minutes):
    """Test round-trip serialization for HoursOfOperationTimeSlice."""
    # Property: to_dict and from_dict should be inverses
    
    original = connect.HoursOfOperationTimeSlice(
        Hours=hours,
        Minutes=minutes
    )
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Create new object from dict
    # Note: _from_dict is a class method
    new_obj = connect.HoursOfOperationTimeSlice._from_dict(**dict_repr)
    
    # They should produce the same dict representation
    assert new_obj.to_dict() == dict_repr


# Test 9: UserPhoneConfig with AfterContactWorkTimeLimit
@given(
    time_limit=st.integers(),
    auto_accept=st.booleans(),
    desk_phone=st.text(),
    phone_type=st.text(min_size=1)
)
def test_user_phone_config(time_limit, auto_accept, desk_phone, phone_type):
    """Test UserPhoneConfig creation and validation."""
    # Property: PhoneType is required, others are optional
    
    config = connect.UserPhoneConfig(
        PhoneType=phone_type
    )
    
    result = config.to_dict()
    assert result["PhoneType"] == phone_type
    
    # Test with optional properties
    config2 = connect.UserPhoneConfig(
        PhoneType=phone_type,
        AfterContactWorkTimeLimit=time_limit,
        AutoAccept=auto_accept,
        DeskPhoneNumber=desk_phone
    )
    
    result2 = config2.to_dict()
    assert result2["PhoneType"] == phone_type
    assert result2["AfterContactWorkTimeLimit"] == time_limit
    assert result2["AutoAccept"] == auto_accept
    if desk_phone:
        assert result2["DeskPhoneNumber"] == desk_phone


# Test 10: UserProficiency with Level as double
@given(
    attr_name=st.text(min_size=1),
    attr_value=st.text(min_size=1),
    level=st.floats(allow_nan=False, allow_infinity=False)
)
def test_user_proficiency(attr_name, attr_value, level):
    """Test UserProficiency with double type for Level."""
    # Property: Level should accept double (float) values
    
    prof = connect.UserProficiency(
        AttributeName=attr_name,
        AttributeValue=attr_value,
        Level=level
    )
    
    result = prof.to_dict()
    assert result["AttributeName"] == attr_name
    assert result["AttributeValue"] == attr_value
    assert result["Level"] == level


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])