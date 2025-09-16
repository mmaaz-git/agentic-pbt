#!/usr/bin/env python3

import sys
import types
import json
from typing import Any

# Mock cfn_flip
sys.modules['cfn_flip'] = types.ModuleType('cfn_flip')

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/worker_/1/troposphere-4.9.3')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import SearchStrategy
import pytest

# Import the modules we're testing
from troposphere.validators import integer
from troposphere.ivschat import (
    Room, 
    LoggingConfiguration, 
    MessageReviewHandler,
    DestinationConfiguration,
    CloudWatchLogsDestinationConfiguration,
    FirehoseDestinationConfiguration,
    S3DestinationConfiguration
)
from troposphere import Tags, BaseAWSObject


# Test 1: The integer validator function
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator_accepts_valid_integers(value):
    """Test that the integer validator properly validates integers.
    
    According to the code, it should:
    1. Accept values that can be converted to int
    2. Return the original value unchanged if valid
    3. Raise ValueError if invalid
    """
    try:
        result = integer(value)
        # If it succeeded, the value should be convertible to int
        int_value = int(value)
        # The validator returns the original value, not the converted int
        assert result == value
    except ValueError as e:
        # Should only raise ValueError for non-integer-convertible values
        try:
            int(value)
            # If int() works but integer() raised ValueError, that's a bug
            pytest.fail(f"integer() raised ValueError for valid integer-convertible value: {value}")
        except (ValueError, TypeError):
            # Expected - value cannot be converted to int
            pass


# Test 2: Test integer validator with edge cases
@given(st.one_of(
    st.just(float('inf')),
    st.just(float('-inf')),
    st.just(float('nan')),
    st.text(min_size=1).filter(lambda x: not x.strip().lstrip('-').isdigit()),
    st.binary(),
    st.complex_numbers()
))
def test_integer_validator_rejects_invalid_values(value):
    """Test that integer validator rejects invalid values."""
    with pytest.raises(ValueError):
        integer(value)


# Test 3: Room property validation
@given(
    max_msg_len=st.one_of(st.none(), st.integers()),
    max_msg_rate=st.one_of(st.none(), st.integers()),
    name=st.one_of(st.none(), st.text(min_size=1)),
    log_ids=st.one_of(st.none(), st.lists(st.text()))
)
def test_room_accepts_valid_properties(max_msg_len, max_msg_rate, name, log_ids):
    """Test that Room accepts valid property types."""
    kwargs = {}
    if max_msg_len is not None:
        kwargs['MaximumMessageLength'] = max_msg_len
    if max_msg_rate is not None:
        kwargs['MaximumMessageRatePerSecond'] = max_msg_rate
    if name is not None:
        kwargs['Name'] = name
    if log_ids is not None:
        kwargs['LoggingConfigurationIdentifiers'] = log_ids
    
    try:
        room = Room('TestRoom', **kwargs)
        # Verify properties were set correctly
        if max_msg_len is not None:
            # The integer validator should have been called
            assert hasattr(room, 'MaximumMessageLength')
        if max_msg_rate is not None:
            assert hasattr(room, 'MaximumMessageRatePerSecond')
    except (ValueError, TypeError) as e:
        # Should only fail if the integer values are invalid
        if max_msg_len is not None:
            try:
                int(max_msg_len)
            except (ValueError, TypeError):
                # Expected failure
                return
        if max_msg_rate is not None:
            try:
                int(max_msg_rate)
            except (ValueError, TypeError):
                # Expected failure
                return
        # If we get here, it failed when it shouldn't have
        pytest.fail(f"Room() raised error for valid inputs: {e}")


# Test 4: Test Room with invalid property types
@given(
    invalid_value=st.one_of(
        st.dictionaries(st.text(), st.integers()),
        st.lists(st.lists(st.text())),
        st.complex_numbers()
    )
)
def test_room_rejects_invalid_integer_properties(invalid_value):
    """Test that Room rejects invalid types for integer properties."""
    # These should fail because they expect integers
    with pytest.raises((ValueError, TypeError)):
        Room('TestRoom', MaximumMessageLength=invalid_value)
    
    with pytest.raises((ValueError, TypeError)):
        Room('TestRoom', MaximumMessageRatePerSecond=invalid_value)


# Test 5: Test JSON serialization round-trip
@given(
    name=st.text(min_size=1, max_size=100),
    max_len=st.integers(min_value=1, max_value=10000),
    max_rate=st.integers(min_value=1, max_value=1000)
)
def test_room_json_serialization_roundtrip(name, max_len, max_rate):
    """Test that Room objects can be serialized to JSON and maintain properties."""
    room = Room(
        'TestRoom',
        Name=name,
        MaximumMessageLength=max_len,
        MaximumMessageRatePerSecond=max_rate
    )
    
    # Convert to dict then to JSON
    room_dict = room.to_dict()
    json_str = json.dumps(room_dict)
    
    # Parse back
    parsed = json.loads(json_str)
    
    # Check that properties are preserved
    assert parsed['Type'] == 'AWS::IVSChat::Room'
    props = parsed.get('Properties', {})
    assert props.get('Name') == name
    assert props.get('MaximumMessageLength') == max_len
    assert props.get('MaximumMessageRatePerSecond') == max_rate


# Test 6: Test LoggingConfiguration with destination configs
@given(
    log_group=st.text(min_size=1, max_size=100),
    delivery_stream=st.text(min_size=1, max_size=100),
    bucket=st.text(min_size=1, max_size=100),
    config_name=st.text(min_size=1, max_size=100)
)
def test_logging_configuration_with_destinations(log_group, delivery_stream, bucket, config_name):
    """Test LoggingConfiguration with various destination configurations."""
    # Create destination configs
    cloudwatch = CloudWatchLogsDestinationConfiguration(LogGroupName=log_group)
    firehose = FirehoseDestinationConfiguration(DeliveryStreamName=delivery_stream)
    s3 = S3DestinationConfiguration(BucketName=bucket)
    
    # Create a destination configuration with all three
    dest_config = DestinationConfiguration(
        CloudWatchLogs=cloudwatch,
        Firehose=firehose,
        S3=s3
    )
    
    # Create logging configuration
    log_config = LoggingConfiguration(
        'TestLogging',
        Name=config_name,
        DestinationConfiguration=dest_config
    )
    
    # Verify it serializes correctly
    config_dict = log_config.to_dict()
    assert config_dict['Type'] == 'AWS::IVSChat::LoggingConfiguration'
    
    props = config_dict['Properties']
    assert props['Name'] == config_name
    
    dest = props['DestinationConfiguration']
    assert dest['CloudWatchLogs']['LogGroupName'] == log_group
    assert dest['Firehose']['DeliveryStreamName'] == delivery_stream
    assert dest['S3']['BucketName'] == bucket


# Test 7: Test MessageReviewHandler properties
@given(
    fallback=st.one_of(st.none(), st.text(min_size=1)),
    uri=st.one_of(st.none(), st.text(min_size=1))
)
def test_message_review_handler(fallback, uri):
    """Test MessageReviewHandler accepts optional properties."""
    kwargs = {}
    if fallback is not None:
        kwargs['FallbackResult'] = fallback
    if uri is not None:
        kwargs['Uri'] = uri
    
    handler = MessageReviewHandler(**kwargs)
    
    # Create a Room with the handler
    room = Room('TestRoom', MessageReviewHandler=handler)
    room_dict = room.to_dict()
    
    if fallback or uri:
        props = room_dict['Properties']
        handler_dict = props.get('MessageReviewHandler', {})
        if fallback:
            assert handler_dict.get('FallbackResult') == fallback
        if uri:
            assert handler_dict.get('Uri') == uri


# Test 8: Test property name validation  
@given(
    invalid_prop_name=st.text(min_size=1).filter(lambda x: x not in [
        'LoggingConfigurationIdentifiers', 'MaximumMessageLength',
        'MaximumMessageRatePerSecond', 'MessageReviewHandler', 'Name', 'Tags'
    ])
)
def test_room_rejects_invalid_property_names(invalid_prop_name):
    """Test that Room rejects invalid property names."""
    with pytest.raises(AttributeError):
        Room('TestRoom', **{invalid_prop_name: 'value'})


# Test 9: Test integer validator with string numbers
@given(st.text().filter(lambda x: x.strip().lstrip('-').replace('.', '', 1).isdigit()))
def test_integer_validator_with_numeric_strings(numeric_str):
    """Test integer validator with numeric strings."""
    try:
        result = integer(numeric_str)
        # Should accept strings that can be converted to integers
        int_value = int(float(numeric_str))  # Handle decimal strings
        assert result == numeric_str
    except ValueError:
        # Should only fail if string cannot be converted to int
        try:
            int(float(numeric_str))
            pytest.fail(f"integer() rejected valid numeric string: {numeric_str}")
        except (ValueError, TypeError):
            # Expected for non-integer strings like "3.14"
            pass


# Test 10: Test empty Room creation
def test_empty_room_creation():
    """Test creating a Room with no properties."""
    room = Room('EmptyRoom')
    room_dict = room.to_dict()
    
    assert room_dict['Type'] == 'AWS::IVSChat::Room'
    # Properties should exist but may be empty
    assert 'Properties' in room_dict or room_dict.get('Properties') == {}


if __name__ == '__main__':
    # Run a quick test to make sure imports work
    print("Running property-based tests for troposphere.ivschat...")
    
    # Run tests with pytest
    import subprocess
    subprocess.run([sys.executable, '-m', 'pytest', __file__, '-v', '--tb=short'])