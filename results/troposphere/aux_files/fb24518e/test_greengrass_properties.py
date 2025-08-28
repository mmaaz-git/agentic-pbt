#!/usr/bin/env python3
"""
Property-based tests for troposphere.greengrass module.
Testing properties explicitly claimed by the code.
"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import troposphere.greengrass as greengrass
from troposphere import AWSObject, AWSProperty


# Strategy for generating valid alphanumeric titles
valid_titles = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=255)

# Strategy for invalid titles (containing non-alphanumeric characters)
invalid_titles = st.text(min_size=1, max_size=100).filter(lambda x: not x.isalnum())


# Test 1: Title validation property - titles must be alphanumeric
@given(title=valid_titles)
def test_valid_title_accepted(title):
    """Valid alphanumeric titles should be accepted"""
    # Try with various Greengrass resource types
    conn_def = greengrass.ConnectorDefinition(title, Name="TestConnector")
    assert conn_def.title == title
    conn_def.to_dict()  # Should not raise


@given(title=invalid_titles)
def test_invalid_title_rejected(title):
    """Non-alphanumeric titles should be rejected during validation"""
    conn_def = greengrass.ConnectorDefinition(title, Name="TestConnector")
    with pytest.raises(ValueError, match="not alphanumeric"):
        conn_def.to_dict()  # Validation happens here


# Test 2: Required properties validation
@given(title=valid_titles)
def test_required_properties_validation(title):
    """Missing required properties should raise ValueError"""
    # ConnectorDefinition requires 'Name' property
    conn_def = greengrass.ConnectorDefinition(title)
    # Don't set the required Name property
    with pytest.raises(ValueError, match="Resource Name required"):
        conn_def.to_dict()


# Test 3: Type validation for string properties
@given(
    title=valid_titles,
    name=st.one_of(
        st.text(min_size=1),  # Valid string
        st.integers(),  # Invalid - should be string
        st.floats(),  # Invalid - should be string
        st.lists(st.text()),  # Invalid - should be string
        st.dictionaries(st.text(), st.text())  # Invalid - should be string
    )
)
def test_type_validation_string_property(title, name):
    """String properties should accept strings and reject other types"""
    if isinstance(name, str):
        # Should succeed for strings
        conn_def = greengrass.ConnectorDefinition(title, Name=name)
        conn_def.to_dict()
    else:
        # Should fail for non-strings
        with pytest.raises(TypeError):
            greengrass.ConnectorDefinition(title, Name=name)


# Test 4: List property validation
@given(
    title=valid_titles,
    connectors=st.one_of(
        st.lists(st.builds(
            greengrass.Connector,
            ConnectorArn=st.text(min_size=1),
            Id=st.text(min_size=1)
        )),  # Valid list
        st.text(),  # Invalid - should be list
        st.integers(),  # Invalid - should be list
        st.builds(
            greengrass.Connector,
            ConnectorArn=st.text(min_size=1),
            Id=st.text(min_size=1)
        )  # Invalid - single item not in list
    )
)
def test_list_property_validation(title, connectors):
    """List properties should accept lists and reject non-lists"""
    conn_def_version = greengrass.ConnectorDefinitionVersion(
        "TestVersion",
        ConnectorDefinitionId="test-id"
    )
    
    if isinstance(connectors, list):
        # Should succeed for lists
        conn_def_version.Connectors = connectors
        conn_def_version.to_dict()
    else:
        # Should fail for non-lists
        with pytest.raises(TypeError):
            conn_def_version.Connectors = connectors


# Test 5: Boolean property validation
@given(
    title=valid_titles,
    sync_shadow=st.one_of(
        st.booleans(),  # Valid
        st.text(),  # Should be coerced
        st.integers(),  # Should be coerced
        st.none()  # Should fail
    )
)
def test_boolean_property_validation(title, sync_shadow):
    """Boolean properties should properly validate/coerce values"""
    core = greengrass.Core(
        "TestCore",
        CertificateArn="arn:test",
        Id="core-id",
        ThingArn="arn:thing"
    )
    
    if sync_shadow is None:
        # None should fail
        with pytest.raises((TypeError, ValueError)):
            core.SyncShadow = sync_shadow
    else:
        # Should succeed or coerce for valid boolean-like values
        core.SyncShadow = sync_shadow
        result = core.to_dict()
        if 'SyncShadow' in result:
            # Check it was properly converted to boolean
            assert isinstance(result['SyncShadow'], (bool, str))


# Test 6: Integer property validation
@given(
    title=valid_titles,
    space=st.one_of(
        st.integers(),  # Valid
        st.floats(allow_nan=False, allow_infinity=False),  # Should be coerced
        st.text(alphabet='0123456789', min_size=1),  # String numbers - should be coerced
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1)  # Invalid strings
    )
)
def test_integer_property_validation(title, space):
    """Integer properties should validate/coerce values appropriately"""
    logger = greengrass.Logger(
        "TestLogger",
        Component="test",
        Id="logger-id",
        Level="INFO",
        Type="FileSystem"
    )
    
    try:
        # Try to convert to int
        int_val = int(space) if not isinstance(space, float) else int(space)
        logger.Space = space
        result = logger.to_dict()
        if 'Space' in result:
            # Should be converted to integer
            assert isinstance(result['Space'], (int, str))
    except (ValueError, TypeError, OverflowError):
        # Should fail for non-convertible values
        with pytest.raises((TypeError, ValueError)):
            logger.Space = space


# Test 7: Serialization round-trip property
@given(
    title=valid_titles,
    name=st.text(min_size=1),
    tags=st.dictionaries(st.text(min_size=1), st.text())
)
def test_serialization_invariant(title, name, tags):
    """Objects should serialize to dict and maintain structure"""
    conn_def = greengrass.ConnectorDefinition(title, Name=name)
    if tags:
        conn_def.Tags = tags
    
    # Serialize to dict
    dict1 = conn_def.to_dict()
    
    # Should be able to serialize again with same result
    dict2 = conn_def.to_dict()
    
    assert dict1 == dict2
    assert dict1['Type'] == 'AWS::Greengrass::ConnectorDefinition'
    assert dict1['Properties']['Name'] == name
    if tags:
        assert dict1['Properties']['Tags'] == tags


# Test 8: Nested property validation
@given(
    title=valid_titles,
    gid=st.one_of(st.integers(), st.text()),
    uid=st.one_of(st.integers(), st.text())
)
def test_nested_property_validation(title, gid, uid):
    """Nested properties should validate their sub-properties"""
    run_as = greengrass.RunAs("TestRunAs")
    
    # Both Gid and Uid should accept integers or be validated
    errors = []
    
    try:
        run_as.Gid = gid
    except (TypeError, ValueError) as e:
        errors.append(('Gid', gid, e))
    
    try:
        run_as.Uid = uid
    except (TypeError, ValueError) as e:
        errors.append(('Uid', uid, e))
    
    # If both are valid integers, to_dict should work
    if not errors:
        try:
            result = run_as.to_dict()
            # Values should be preserved or converted
            if hasattr(run_as, 'Gid'):
                assert 'Gid' in result
            if hasattr(run_as, 'Uid'):
                assert 'Uid' in result
        except (TypeError, ValueError):
            # Validation might fail on to_dict if validators are strict
            pass


# Test 9: Resource type consistency
@given(title=valid_titles, name=st.text(min_size=1))
def test_resource_type_consistency(title, name):
    """Resource types should be correctly set and maintained"""
    resources_to_test = [
        (greengrass.ConnectorDefinition(title, Name=name), "AWS::Greengrass::ConnectorDefinition"),
        (greengrass.CoreDefinition(title, Name=name), "AWS::Greengrass::CoreDefinition"),
        (greengrass.DeviceDefinition(title, Name=name), "AWS::Greengrass::DeviceDefinition"),
        (greengrass.FunctionDefinition(title, Name=name), "AWS::Greengrass::FunctionDefinition"),
        (greengrass.Group(title, Name=name), "AWS::Greengrass::Group"),
        (greengrass.LoggerDefinition(title, Name=name), "AWS::Greengrass::LoggerDefinition"),
        (greengrass.ResourceDefinition(title, Name=name), "AWS::Greengrass::ResourceDefinition"),
        (greengrass.SubscriptionDefinition(title, Name=name), "AWS::Greengrass::SubscriptionDefinition"),
    ]
    
    for resource, expected_type in resources_to_test:
        assert resource.resource_type == expected_type
        dict_repr = resource.to_dict()
        assert dict_repr['Type'] == expected_type


# Test 10: Property inheritance
@given(title=valid_titles)
def test_awsobject_awsproperty_distinction(title):
    """AWSObject and AWSProperty should behave differently in serialization"""
    # AWSObject should have a Type field
    obj = greengrass.ConnectorDefinition(title, Name="test")
    obj_dict = obj.to_dict()
    assert 'Type' in obj_dict
    assert obj_dict['Type'] == 'AWS::Greengrass::ConnectorDefinition'
    
    # AWSProperty should not have a Type field
    prop = greengrass.Connector("TestProp", ConnectorArn="arn:test", Id="test-id")
    prop_dict = prop.to_dict()
    assert 'Type' not in prop_dict
    assert 'ConnectorArn' in prop_dict
    assert 'Id' in prop_dict


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    pytest.main([__file__, "-v", "--tb=short"])