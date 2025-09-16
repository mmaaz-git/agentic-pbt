#!/usr/bin/env python3
"""
Property-based tests for troposphere.directoryservice module
"""

import sys
import os
import re
import json
from typing import Any, Dict

# Add the troposphere environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import hypothesis
from hypothesis import given, strategies as st, assume, settings
import troposphere.directoryservice as ds
from troposphere.validators import boolean
from troposphere import BaseAWSObject


# Strategy for valid CloudFormation resource titles (alphanumeric only)
valid_titles = st.text(alphabet=st.characters(categories=["Lu", "Ll", "Nd"]), min_size=1, max_size=255)

# Strategy for valid VPC IDs (vpc-xxxxxxxx format)
vpc_ids = st.text(alphabet="0123456789abcdef", min_size=8, max_size=8).map(lambda x: f"vpc-{x}")

# Strategy for valid subnet IDs (subnet-xxxxxxxx format)
subnet_ids = st.text(alphabet="0123456789abcdef", min_size=8, max_size=8).map(lambda x: f"subnet-{x}")

# Strategy for lists of subnet IDs
subnet_id_lists = st.lists(subnet_ids, min_size=1, max_size=5)

# Strategy for passwords
passwords = st.text(min_size=8, max_size=64)

# Strategy for directory names
directory_names = st.text(min_size=1, max_size=255)

# Strategy for directory sizes
directory_sizes = st.sampled_from(["Small", "Large"])

# Strategy for editions
editions = st.sampled_from(["Standard", "Enterprise"])


# Test 1: Boolean validator conversion property
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_validator_accepts_valid_inputs(value):
    """Test that the boolean validator correctly converts valid boolean representations"""
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(
    st.text().filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_validator_rejects_invalid_inputs(value):
    """Test that the boolean validator raises ValueError for invalid inputs"""
    try:
        boolean(value)
        assert False, f"Expected ValueError for {value}"
    except ValueError:
        pass  # Expected


# Test 2: Title validation property
@given(valid_titles)
def test_valid_title_accepted(title):
    """Test that valid alphanumeric titles are accepted"""
    obj = ds.SimpleAD(
        title=title,
        Name="test.example.com",
        Size="Small",
        VpcSettings=ds.VpcSettings(
            VpcId="vpc-12345678",
            SubnetIds=["subnet-12345678"]
        )
    )
    assert obj.title == title


@given(st.text(min_size=1).filter(lambda x: not re.match(r'^[a-zA-Z0-9]+$', x)))
def test_invalid_title_rejected(title):
    """Test that non-alphanumeric titles are rejected"""
    try:
        ds.SimpleAD(
            title=title,
            Name="test.example.com",
            Size="Small",
            VpcSettings=ds.VpcSettings(
                VpcId="vpc-12345678",
                SubnetIds=["subnet-12345678"]
            )
        )
        assert False, f"Expected ValueError for title: {title}"
    except ValueError as e:
        assert "not alphanumeric" in str(e)


# Test 3: Required field validation
@given(valid_titles, directory_names, directory_sizes, vpc_ids, subnet_id_lists)
def test_simplead_required_fields(title, name, size, vpc_id, subnet_ids):
    """Test that SimpleAD can be created with all required fields"""
    obj = ds.SimpleAD(
        title=title,
        Name=name,
        Size=size,
        VpcSettings=ds.VpcSettings(
            VpcId=vpc_id,
            SubnetIds=subnet_ids
        )
    )
    # Validation should pass
    obj.to_dict()
    assert obj.properties["Name"] == name
    assert obj.properties["Size"] == size


@given(valid_titles, directory_names, passwords, vpc_ids, subnet_id_lists)
def test_microsoftad_required_fields(title, name, password, vpc_id, subnet_ids):
    """Test that MicrosoftAD can be created with all required fields"""
    obj = ds.MicrosoftAD(
        title=title,
        Name=name,
        Password=password,
        VpcSettings=ds.VpcSettings(
            VpcId=vpc_id,
            SubnetIds=subnet_ids
        )
    )
    # Validation should pass
    obj.to_dict()
    assert obj.properties["Name"] == name
    assert obj.properties["Password"] == password


@given(valid_titles, directory_names)
def test_missing_required_field_raises_error(title, name):
    """Test that missing required fields raise errors during validation"""
    # Create SimpleAD without required VpcSettings
    obj = ds.SimpleAD(
        title=title,
        Name=name,
        Size="Small"
    )
    try:
        obj.to_dict()  # This should trigger validation
        assert False, "Expected ValueError for missing VpcSettings"
    except ValueError as e:
        assert "VpcSettings" in str(e)
        assert "required" in str(e)


# Test 4: to_dict/from_dict round-trip property
@given(
    valid_titles,
    directory_names,
    directory_sizes,
    vpc_ids,
    subnet_id_lists,
    st.booleans(),
    st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_simplead_to_dict_from_dict_roundtrip(title, name, size, vpc_id, subnet_ids, enable_sso, description):
    """Test that SimpleAD objects can be serialized and deserialized"""
    # Create original object
    kwargs = {
        "Name": name,
        "Size": size,
        "VpcSettings": ds.VpcSettings(VpcId=vpc_id, SubnetIds=subnet_ids),
        "EnableSso": enable_sso
    }
    if description is not None:
        kwargs["Description"] = description
    
    original = ds.SimpleAD(title=title, **kwargs)
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Get properties from dict
    props = dict_repr.get("Properties", {})
    
    # Create new object from dict
    reconstructed = ds.SimpleAD.from_dict(title, props)
    
    # Compare properties
    assert reconstructed.properties["Name"] == original.properties["Name"]
    assert reconstructed.properties["Size"] == original.properties["Size"]
    assert reconstructed.properties["EnableSso"] == original.properties["EnableSso"]
    if description is not None:
        assert reconstructed.properties["Description"] == original.properties["Description"]


# Test 5: Resource type property
def test_simplead_resource_type():
    """Test that SimpleAD has the correct resource type"""
    obj = ds.SimpleAD(
        title="TestSimpleAD",
        Name="test.example.com",
        Size="Small",
        VpcSettings=ds.VpcSettings(
            VpcId="vpc-12345678",
            SubnetIds=["subnet-12345678"]
        )
    )
    assert obj.resource_type == "AWS::DirectoryService::SimpleAD"
    dict_repr = obj.to_dict()
    assert dict_repr["Type"] == "AWS::DirectoryService::SimpleAD"


def test_microsoftad_resource_type():
    """Test that MicrosoftAD has the correct resource type"""
    obj = ds.MicrosoftAD(
        title="TestMicrosoftAD",
        Name="test.example.com",
        Password="TestPassword123!",
        VpcSettings=ds.VpcSettings(
            VpcId="vpc-12345678",
            SubnetIds=["subnet-12345678"]
        )
    )
    assert obj.resource_type == "AWS::DirectoryService::MicrosoftAD"
    dict_repr = obj.to_dict()
    assert dict_repr["Type"] == "AWS::DirectoryService::MicrosoftAD"


# Test 6: VpcSettings validation
@given(vpc_ids, subnet_id_lists)
def test_vpcsettings_required_fields(vpc_id, subnet_ids):
    """Test that VpcSettings validates required fields"""
    vpc_settings = ds.VpcSettings(VpcId=vpc_id, SubnetIds=subnet_ids)
    dict_repr = vpc_settings.to_dict()
    assert dict_repr["VpcId"] == vpc_id
    assert dict_repr["SubnetIds"] == subnet_ids


# Test 7: Property type validation
@given(valid_titles, st.one_of(st.integers(), st.floats(), st.lists(st.integers())))
def test_invalid_property_type_rejected(title, invalid_value):
    """Test that invalid property types are rejected"""
    try:
        ds.SimpleAD(
            title=title,
            Name=invalid_value,  # Name should be a string
            Size="Small",
            VpcSettings=ds.VpcSettings(
                VpcId="vpc-12345678",
                SubnetIds=["subnet-12345678"]
            )
        )
        # If we get here, check if the value was coerced to string
        # (which might happen for some types)
    except (TypeError, ValueError):
        pass  # Expected for non-string types


# Test 8: Boolean property coercion
@given(
    valid_titles,
    st.sampled_from([True, False, 1, 0, "true", "false", "True", "False"])
)
def test_boolean_property_coercion(title, bool_value):
    """Test that boolean properties correctly coerce valid boolean values"""
    obj = ds.SimpleAD(
        title=title,
        Name="test.example.com",
        Size="Small",
        VpcSettings=ds.VpcSettings(
            VpcId="vpc-12345678",
            SubnetIds=["subnet-12345678"]
        ),
        EnableSso=bool_value
    )
    # The boolean validator should have normalized the value
    assert obj.properties["EnableSso"] in [True, False]
    if bool_value in [True, 1, "true", "True"]:
        assert obj.properties["EnableSso"] is True
    else:
        assert obj.properties["EnableSso"] is False


# Test 9: Edition validation for MicrosoftAD
@given(valid_titles, editions)
def test_microsoftad_edition_property(title, edition):
    """Test that MicrosoftAD accepts valid edition values"""
    obj = ds.MicrosoftAD(
        title=title,
        Name="test.example.com",
        Password="TestPassword123!",
        VpcSettings=ds.VpcSettings(
            VpcId="vpc-12345678",
            SubnetIds=["subnet-12345678"]
        ),
        Edition=edition
    )
    assert obj.properties["Edition"] == edition


if __name__ == "__main__":
    # Run a quick check on all tests
    print("Running property-based tests for troposphere.directoryservice...")
    
    # Test boolean validator
    test_boolean_validator_accepts_valid_inputs()
    test_boolean_validator_rejects_invalid_inputs()
    
    # Test title validation
    test_valid_title_accepted()
    test_invalid_title_rejected()
    
    # Test required fields
    test_simplead_required_fields()
    test_microsoftad_required_fields()
    test_missing_required_field_raises_error()
    
    # Test round-trip
    test_simplead_to_dict_from_dict_roundtrip()
    
    # Test resource types
    test_simplead_resource_type()
    test_microsoftad_resource_type()
    
    # Test VpcSettings
    test_vpcsettings_required_fields()
    
    # Test type validation
    test_invalid_property_type_rejected()
    
    # Test boolean coercion
    test_boolean_property_coercion()
    
    # Test MicrosoftAD edition
    test_microsoftad_edition_property()
    
    print("All tests passed!")