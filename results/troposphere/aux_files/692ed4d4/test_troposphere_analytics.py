#!/usr/bin/env python3
"""Property-based tests for troposphere.analytics module"""

import sys
import json
import re
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere
from troposphere import analytics, validators
from troposphere import AWSObject, AWSProperty, BaseAWSObject


# Test 1: Title validation property - titles must be alphanumeric
@given(st.text())
def test_title_validation(title):
    """Test that title validation correctly accepts only alphanumeric titles"""
    try:
        app = analytics.Application(title)
        # If it succeeds, title should be alphanumeric
        assert re.match(r'^[a-zA-Z0-9]+$', title) is not None
    except ValueError as e:
        # If it fails, title should NOT be alphanumeric
        if 'not alphanumeric' in str(e):
            assert re.match(r'^[a-zA-Z0-9]+$', title) is None


# Test 2: Integer validator property
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans(),
    st.none()
))
def test_integer_validator(value):
    """Test that integer validator accepts exactly what can be converted to int"""
    try:
        result = validators.integer(value)
        # If it succeeds, int(value) should work
        int(value)
    except (ValueError, TypeError):
        # If either fails, both should fail
        with pytest.raises((ValueError, TypeError)):
            int(value)


# Test 3: Positive integer validator
@given(st.integers())
def test_positive_integer_validator(value):
    """Test that positive_integer accepts only non-negative integers"""
    try:
        result = validators.positive_integer(value)
        # If it succeeds, value should be >= 0
        assert value >= 0
    except ValueError:
        # If it fails, value should be < 0
        assert value < 0


# Test 4: Boolean validator conversions
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False"),
    st.text(), st.integers(), st.none()
))
def test_boolean_validator(value):
    """Test that boolean validator correctly maps specific values"""
    try:
        result = validators.boolean(value)
        if value in [True, 1, "1", "true", "True"]:
            assert result is True
        elif value in [False, 0, "0", "false", "False"]:
            assert result is False
        else:
            # Should not reach here if validator works correctly
            assert False, f"Unexpected success for value: {value}"
    except ValueError:
        # Should only fail for values not in the lists
        assert value not in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]


# Test 5: Network port validator
@given(st.integers())
def test_network_port_validator(port):
    """Test that network_port validator accepts ports between -1 and 65535"""
    try:
        result = validators.network_port(port)
        # If it succeeds, port should be in valid range
        assert -1 <= port <= 65535
    except ValueError as e:
        # If it fails with port error, should be out of range
        if 'between 0 and 65535' in str(e):
            assert port < -1 or port > 65535


# Test 6: S3 bucket name validator - no consecutive dots property
@given(st.text(min_size=2, max_size=63, alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters=".-")))
def test_s3_bucket_consecutive_dots(name):
    """Test that S3 bucket validator rejects names with consecutive dots"""
    try:
        result = validators.s3_bucket_name(name)
        # If it succeeds, should not have consecutive dots
        assert ".." not in name
    except ValueError as e:
        # Could fail for multiple reasons, check if it's due to dots
        if ".." in name:
            # If it has consecutive dots, it should fail
            assert True
        # Else it failed for another reason (IP address, regex mismatch, etc.)


# Test 7: S3 bucket name validator - no IP addresses
@given(st.from_regex(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', fullmatch=True))
def test_s3_bucket_ip_address(name):
    """Test that S3 bucket validator rejects IP addresses"""
    # All generated strings should look like IP addresses
    try:
        result = validators.s3_bucket_name(name)
        # Should never succeed for IP addresses
        assert False, f"S3 validator accepted IP address: {name}"
    except ValueError:
        # Should always fail for IP addresses
        assert True


# Test 8: JSON checker property - roundtrip for dicts
@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(st.integers(), st.text(), st.booleans(), st.none()),
    max_size=10
))
def test_json_checker_dict_roundtrip(data):
    """Test that json_checker correctly converts dicts to JSON strings"""
    result = validators.json_checker(data)
    # Result should be a JSON string
    assert isinstance(result, str)
    # Should be able to parse it back
    parsed = json.loads(result)
    assert parsed == data


# Test 9: JSON checker property - valid JSON strings pass through
@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(st.integers(), st.text(), st.booleans(), st.none()),
    max_size=10
))
def test_json_checker_string_passthrough(data):
    """Test that json_checker accepts valid JSON strings"""
    json_str = json.dumps(data)
    result = validators.json_checker(json_str)
    # Should return the same string
    assert result == json_str
    # Should be valid JSON
    assert json.loads(result) == data


# Test 10: Required properties validation in analytics classes
@given(
    st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=1, max_size=20),  # Valid title
    st.text(),  # ResourceARN
    st.text()   # RoleARN
)
def test_required_properties_validation(title, resource_arn, role_arn):
    """Test that required properties are enforced in analytics classes"""
    # InputLambdaProcessor requires ResourceARN and RoleARN
    try:
        # Try creating without required properties
        processor = analytics.InputLambdaProcessor()
        # Should fail during validation
        processor.to_dict()
        assert False, "Should have raised ValueError for missing required properties"
    except ValueError as e:
        assert "required" in str(e).lower()
    
    # With required properties, should work
    processor = analytics.InputLambdaProcessor(
        ResourceARN=resource_arn,
        RoleARN=role_arn
    )
    # Should succeed
    result = processor.to_dict()
    assert result["ResourceARN"] == resource_arn
    assert result["RoleARN"] == role_arn


# Test 11: RecordColumn SqlType is required
@given(
    st.text(min_size=1),  # Name
    st.text(min_size=1),  # SqlType
    st.text()  # Mapping (optional)
)
def test_record_column_required_fields(name, sql_type, mapping):
    """Test that RecordColumn enforces required Name and SqlType fields"""
    # Should succeed with required fields
    col = analytics.RecordColumn(Name=name, SqlType=sql_type)
    result = col.to_dict()
    assert result["Name"] == name
    assert result["SqlType"] == sql_type
    
    # Test optional field
    col_with_mapping = analytics.RecordColumn(Name=name, SqlType=sql_type, Mapping=mapping)
    result = col_with_mapping.to_dict()
    assert result["Mapping"] == mapping


# Test 12: Integer properties accept strings that can be converted to int
@given(st.integers(min_value=-1000, max_value=1000))
def test_integer_property_string_conversion(value):
    """Test that integer properties accept string representations of integers"""
    # InputParallelism has a Count property that uses integer validator
    # Test with integer
    parallelism1 = analytics.InputParallelism(Count=value)
    
    # Test with string representation
    parallelism2 = analytics.InputParallelism(Count=str(value))
    
    # Both should produce the same result
    assert parallelism1.to_dict()["Count"] == value
    assert parallelism2.to_dict()["Count"] == str(value)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])