#!/usr/bin/env python3
"""Property-based tests for troposphere library using Hypothesis."""

import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere
from troposphere import Template, Parameter, Output, BaseAWSObject, AWSObject
from troposphere.validators import (
    s3_bucket_name, positive_integer, integer, boolean, 
    integer_range, network_port, json_checker
)


# Test 1: S3 bucket name validation properties
@given(st.text(min_size=1, max_size=63))
def test_s3_bucket_consecutive_periods(name):
    """S3 bucket names with consecutive periods should always be rejected."""
    if ".." in name:
        try:
            s3_bucket_name(name)
            assert False, f"Should have rejected bucket name with consecutive periods: {name}"
        except ValueError as e:
            assert "not a valid s3 bucket name" in str(e)


@given(st.from_regex(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"))
def test_s3_bucket_ip_address_rejected(ip_like_name):
    """S3 bucket names that look like IP addresses should always be rejected."""
    try:
        s3_bucket_name(ip_like_name)
        assert False, f"Should have rejected IP-like bucket name: {ip_like_name}"
    except ValueError as e:
        assert "not a valid s3 bucket name" in str(e)


@given(st.from_regex(r"^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$").filter(
    lambda s: ".." not in s and not s.replace(".", "").replace("-", "").isdigit()
))
def test_s3_bucket_valid_names_accepted(name):
    """Valid S3 bucket names matching the regex should be accepted."""
    # Filter out IP-like patterns
    parts = name.split(".")
    if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        return  # Skip IP addresses
    
    result = s3_bucket_name(name)
    assert result == name


# Test 2: Integer validator properties
@given(st.integers())
def test_positive_integer_rejects_negative(x):
    """positive_integer should reject all negative integers."""
    if x < 0:
        try:
            positive_integer(x)
            assert False, f"Should have rejected negative integer: {x}"
        except ValueError as e:
            assert "not a positive integer" in str(e)
    else:
        result = positive_integer(x)
        assert result == x


@given(st.integers(min_value=-100000, max_value=100000))
def test_integer_range_invariant(x):
    """integer_range validator should enforce min/max bounds correctly."""
    min_val, max_val = 10, 100
    validator = integer_range(min_val, max_val)
    
    if min_val <= x <= max_val:
        result = validator(x)
        assert result == x
    else:
        try:
            validator(x)
            assert False, f"Should have rejected {x} outside range [{min_val}, {max_val}]"
        except ValueError as e:
            assert "Integer must be between" in str(e)


# Test 3: Boolean validator confluence property
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_validator_consistency(value):
    """Boolean validator should map all true-like values to True and false-like to False."""
    result = boolean(value)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


# Test 4: Network port validation
@given(st.integers())
def test_network_port_range(port):
    """Network ports must be between -1 and 65535."""
    if -1 <= port <= 65535:
        result = network_port(port)
        assert result == port
    else:
        try:
            network_port(port)
            assert False, f"Should have rejected port {port}"
        except ValueError as e:
            assert "must been between 0 and 65535" in str(e) or "must be between 0 and 65535" in str(e)


# Test 5: Template resource limits
@given(st.integers(min_value=0, max_value=600))
def test_template_max_resources(num_resources):
    """Template should enforce MAX_RESOURCES limit of 500."""
    t = Template()
    
    # Add resources up to the limit
    for i in range(min(num_resources, troposphere.MAX_RESOURCES)):
        # Create a simple resource
        class DummyResource(AWSObject):
            resource_type = "AWS::CloudFormation::WaitConditionHandle"
            props = {}
        
        resource = DummyResource(f"Resource{i}")
        t.add_resource(resource)
    
    # Try to add one more if we're at or above the limit
    if num_resources > troposphere.MAX_RESOURCES:
        try:
            resource = DummyResource(f"Resource{troposphere.MAX_RESOURCES}")
            t.add_resource(resource)
            assert False, f"Should have rejected adding resource #{troposphere.MAX_RESOURCES + 1}"
        except ValueError as e:
            assert "Maximum number of resources" in str(e)


@given(st.integers(min_value=0, max_value=250))  
def test_template_max_parameters(num_params):
    """Template should enforce MAX_PARAMETERS limit of 200."""
    t = Template()
    
    # Add parameters up to the limit
    for i in range(min(num_params, troposphere.MAX_PARAMETERS)):
        param = Parameter(f"Param{i}", Type="String")
        t.add_parameter(param)
    
    # Try to add one more if we're at or above the limit
    if num_params > troposphere.MAX_PARAMETERS:
        try:
            param = Parameter(f"Param{troposphere.MAX_PARAMETERS}", Type="String")
            t.add_parameter(param)
            assert False, f"Should have rejected adding parameter #{troposphere.MAX_PARAMETERS + 1}"
        except ValueError as e:
            assert "Maximum parameters" in str(e)


# Test 6: JSON checker round-trip property
@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(st.integers(), st.text(), st.booleans(), st.none()),
    max_size=10
))
def test_json_checker_dict_roundtrip(data):
    """json_checker should convert dict to JSON string and back."""
    json_str = json_checker(data)
    assert isinstance(json_str, str)
    # Verify it's valid JSON that round-trips
    parsed = json.loads(json_str)
    assert parsed == data


@given(st.text().filter(lambda s: s.strip() != ""))
def test_json_checker_string_validation(text):
    """json_checker should validate JSON strings."""
    # Create a valid JSON string
    valid_json = json.dumps({"key": text})
    result = json_checker(valid_json)
    assert result == valid_json
    assert json.loads(result) == {"key": text}


# Test 7: Parameter title length validation
@given(st.text(min_size=256, max_size=300))
def test_parameter_title_max_length(title):
    """Parameter titles cannot exceed 255 characters."""
    try:
        param = Parameter(title, Type="String")
        assert False, f"Should have rejected parameter title of length {len(title)}"
    except ValueError as e:
        assert "can be no longer than" in str(e) and "255" in str(e)


@given(st.text(min_size=1, max_size=255).filter(lambda s: s.replace("a", "").replace("A", "").replace("0", "") == s[:0]))
def test_parameter_title_valid_length(title):
    """Parameter titles up to 255 alphanumeric characters should be accepted."""
    # Ensure title is alphanumeric
    title = "".join(c for c in title if c.isalnum())[:255]
    if title and title.isalnum():
        param = Parameter(title, Type="String")
        assert param.title == title


# Test 8: encode_to_dict idempotence
@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(st.integers(), st.text(), st.lists(st.integers())),
    max_size=5
))
def test_encode_to_dict_idempotent(data):
    """encode_to_dict should be idempotent - applying it twice gives same result."""
    from troposphere import encode_to_dict
    
    once = encode_to_dict(data)
    twice = encode_to_dict(once)
    assert once == twice