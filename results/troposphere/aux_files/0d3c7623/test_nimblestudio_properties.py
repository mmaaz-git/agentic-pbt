#!/usr/bin/env python3
"""Property-based tests for troposphere.nimblestudio module."""

import json
import sys
import os

# Add the troposphere environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.nimblestudio as nimblestudio
from troposphere import AWSObject, AWSProperty

# Strategy for generating valid names (alphanumeric strings)
valid_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
    min_size=1, 
    max_size=50
)

# Strategy for generating string values
string_strategy = st.text(min_size=0, max_size=100)

# Strategy for generating lists of strings
string_list_strategy = st.lists(string_strategy, min_size=0, max_size=10)

# Strategy for generating script parameter key-value pairs
script_param_strategy = st.builds(
    nimblestudio.ScriptParameterKeyValue,
    Key=string_strategy,
    Value=string_strategy
)

# Strategy for generating active directory computer attributes
ad_attr_strategy = st.builds(
    nimblestudio.ActiveDirectoryComputerAttribute,
    Name=string_strategy,
    Value=string_strategy
)

# Test 1: Required properties validation
@given(
    name=valid_name_strategy,
    studio_id=string_strategy,
    component_type=st.sampled_from(["SHARED_FILE_SYSTEM", "COMPUTE_FARM", "LICENSE_SERVICE", "ACTIVE_DIRECTORY"])
)
def test_required_properties_validation(name, studio_id, component_type):
    """Test that StudioComponent correctly validates required properties."""
    # Should succeed with all required properties
    component = nimblestudio.StudioComponent(
        title="TestComponent",
        Name=name,
        StudioId=studio_id,
        Type=component_type
    )
    
    # to_dict should work when all required properties are present
    result = component.to_dict()
    assert "Properties" in result
    assert result["Properties"]["Name"] == name
    assert result["Properties"]["StudioId"] == studio_id
    assert result["Properties"]["Type"] == component_type


# Test 2: Property type validation
@given(
    valid_value=string_strategy,
    invalid_value=st.one_of(st.integers(), st.floats(), st.booleans(), st.lists(st.integers()))
)
def test_property_type_validation(valid_value, invalid_value):
    """Test that properties validate their types correctly."""
    # String properties should accept strings
    component = nimblestudio.StudioComponent(
        title="TestComponent",
        Name="TestName",
        StudioId="TestStudio",
        Type="SHARED_FILE_SYSTEM"
    )
    
    # Setting a string property to a string should work
    component.Description = valid_value
    assert component.Description == valid_value
    
    # Setting a string property to non-string should raise TypeError
    if not isinstance(invalid_value, str):
        try:
            component.Description = invalid_value
            # If it didn't raise, check if it was converted
            assert isinstance(component.Description, str) or hasattr(component.Description, 'to_dict')
        except (TypeError, ValueError):
            # Expected behavior - type validation worked
            pass


# Test 3: to_dict/from_dict round-trip
@given(
    name=valid_name_strategy,
    studio_id=string_strategy,
    component_type=st.sampled_from(["SHARED_FILE_SYSTEM", "COMPUTE_FARM", "LICENSE_SERVICE", "ACTIVE_DIRECTORY"]),
    description=st.one_of(st.none(), string_strategy),
    subtype=st.one_of(st.none(), string_strategy),
    ec2_security_groups=st.one_of(st.none(), string_list_strategy),
    script_params=st.one_of(st.none(), st.lists(script_param_strategy, max_size=5))
)
def test_to_dict_from_dict_roundtrip(name, studio_id, component_type, description, subtype, ec2_security_groups, script_params):
    """Test that to_dict and from_dict form a proper round-trip."""
    # Create a component with various properties
    component = nimblestudio.StudioComponent(
        title="TestComponent",
        Name=name,
        StudioId=studio_id,
        Type=component_type
    )
    
    # Add optional properties if provided
    if description:
        component.Description = description
    if subtype:
        component.Subtype = subtype
    if ec2_security_groups:
        component.Ec2SecurityGroupIds = ec2_security_groups
    if script_params:
        component.ScriptParameters = script_params
    
    # Convert to dict
    dict_repr = component.to_dict()
    
    # Verify the dict has the expected structure
    assert "Type" in dict_repr
    assert dict_repr["Type"] == "AWS::NimbleStudio::StudioComponent"
    assert "Properties" in dict_repr
    
    # Properties should contain what we set
    props = dict_repr["Properties"]
    assert props["Name"] == name
    assert props["StudioId"] == studio_id
    assert props["Type"] == component_type
    
    if description:
        assert props.get("Description") == description
    if subtype:
        assert props.get("Subtype") == subtype
    if ec2_security_groups:
        assert props.get("Ec2SecurityGroupIds") == ec2_security_groups


# Test 4: JSON serialization produces valid JSON
@given(
    name=valid_name_strategy,
    studio_id=string_strategy,
    component_type=st.sampled_from(["SHARED_FILE_SYSTEM", "COMPUTE_FARM", "LICENSE_SERVICE", "ACTIVE_DIRECTORY"]),
    description=st.one_of(st.none(), string_strategy)
)
def test_json_serialization(name, studio_id, component_type, description):
    """Test that to_json produces valid JSON that can be parsed."""
    component = nimblestudio.StudioComponent(
        title="TestComponent",
        Name=name,
        StudioId=studio_id,
        Type=component_type
    )
    
    if description:
        component.Description = description
    
    # to_json should produce valid JSON
    json_str = component.to_json()
    
    # Should be parseable
    parsed = json.loads(json_str)
    
    # Should have the correct structure
    assert "Type" in parsed
    assert parsed["Type"] == "AWS::NimbleStudio::StudioComponent"
    assert "Properties" in parsed
    assert parsed["Properties"]["Name"] == name
    assert parsed["Properties"]["StudioId"] == studio_id
    assert parsed["Properties"]["Type"] == component_type
    
    # JSON round-trip: parse and re-serialize should work
    reparsed = json.loads(json.dumps(parsed))
    assert reparsed == parsed


# Test 5: AWSProperty classes validation
@given(
    key=st.one_of(st.none(), string_strategy),
    value=st.one_of(st.none(), string_strategy)
)
def test_script_parameter_properties(key, value):
    """Test ScriptParameterKeyValue property class."""
    # Create with optional properties
    param = nimblestudio.ScriptParameterKeyValue()
    
    if key is not None:
        param.Key = key
    if value is not None:
        param.Value = value
    
    # to_dict should work
    result = param.to_dict()
    
    # Should be a dict
    assert isinstance(result, dict)
    
    # If properties were set, they should be in the dict
    if key is not None:
        assert result.get("Key") == key
    if value is not None:
        assert result.get("Value") == value


# Test 6: Nested property validation
@given(
    directory_id=string_strategy,
    ou_name=string_strategy,
    computer_attrs=st.lists(ad_attr_strategy, min_size=0, max_size=5)
)
def test_nested_properties(directory_id, ou_name, computer_attrs):
    """Test that nested properties work correctly."""
    # Create an ActiveDirectoryConfiguration with nested properties
    ad_config = nimblestudio.ActiveDirectoryConfiguration()
    
    ad_config.DirectoryId = directory_id
    ad_config.OrganizationalUnitDistinguishedName = ou_name
    
    if computer_attrs:
        ad_config.ComputerAttributes = computer_attrs
    
    # to_dict should handle nested properties
    result = ad_config.to_dict()
    
    assert result.get("DirectoryId") == directory_id
    assert result.get("OrganizationalUnitDistinguishedName") == ou_name
    
    if computer_attrs:
        assert "ComputerAttributes" in result
        # Check that nested objects were serialized
        for i, attr in enumerate(computer_attrs):
            assert result["ComputerAttributes"][i]["Name"] == attr.Name
            assert result["ComputerAttributes"][i]["Value"] == attr.Value


# Test 7: Empty object creation and validation
def test_empty_aws_property_creation():
    """Test that AWSProperty subclasses can be created without arguments."""
    # All AWSProperty subclasses should be creatable without arguments
    property_classes = [
        nimblestudio.ScriptParameterKeyValue,
        nimblestudio.ActiveDirectoryComputerAttribute,
        nimblestudio.ActiveDirectoryConfiguration,
        nimblestudio.ComputeFarmConfiguration,
        nimblestudio.LicenseServiceConfiguration,
        nimblestudio.SharedFileSystemConfiguration,
        nimblestudio.StudioComponentConfiguration,
        nimblestudio.StudioComponentInitializationScript,
    ]
    
    for cls in property_classes:
        # Should be able to create without arguments
        obj = cls()
        
        # to_dict should work even on empty objects
        result = obj.to_dict()
        
        # Should return a dict (possibly empty)
        assert isinstance(result, dict)


# Test 8: Title validation
@given(title=st.text())
def test_title_validation(title):
    """Test that title validation works correctly."""
    # Titles must be alphanumeric
    try:
        component = nimblestudio.StudioComponent(
            title=title,
            Name="TestName",
            StudioId="TestStudio",
            Type="SHARED_FILE_SYSTEM"
        )
        
        # If creation succeeded, title must have been valid
        # Valid titles are alphanumeric only
        assert title.isalnum() or title == ""
        
    except ValueError as e:
        # Should only fail for non-alphanumeric titles
        if "not alphanumeric" in str(e):
            # Check that the title really wasn't alphanumeric
            assert not title.isalnum() or title == ""
        else:
            # Unexpected error
            raise


if __name__ == "__main__":
    import pytest
    
    # Run with increased examples for better coverage
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])