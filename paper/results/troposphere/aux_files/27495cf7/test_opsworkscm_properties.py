#!/usr/bin/env python3
"""Property-based tests for troposphere.opsworkscm module"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.opsworkscm as opsworkscm
from troposphere import Tags, Ref


# Strategies for generating valid input data
alphanumeric_str = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50)
optional_str = st.one_of(st.none(), st.text(min_size=0, max_size=100))
boolean_strategy = st.one_of(st.booleans(), st.sampled_from([0, 1, "true", "false", "True", "False"]))
integer_strategy = st.one_of(st.integers(min_value=0, max_value=1000), st.text().map(str))


@given(
    name=optional_str,
    value=optional_str
)
def test_engine_attribute_roundtrip(name, value):
    """Test that EngineAttribute objects can round-trip through to_dict/from_dict"""
    # Create the object with optional fields
    kwargs = {}
    if name is not None:
        kwargs['Name'] = name
    if value is not None:
        kwargs['Value'] = value
    
    # Create the original object
    original = opsworkscm.EngineAttribute(**kwargs)
    
    # Convert to dict and back
    as_dict = original.to_dict()
    reconstructed = opsworkscm.EngineAttribute.from_dict(None, as_dict)
    
    # They should be equal
    assert original == reconstructed
    assert original.to_dict() == reconstructed.to_dict()


@given(
    title=alphanumeric_str,
    instance_profile_arn=st.text(min_size=1),
    instance_type=st.text(min_size=1),  
    service_role_arn=st.text(min_size=1),
    backup_retention_count=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
    server_name=st.one_of(st.none(), alphanumeric_str)
)
def test_server_roundtrip_with_required_fields(title, instance_profile_arn, instance_type, 
                                                service_role_arn, backup_retention_count, server_name):
    """Test Server round-trip with required fields"""
    kwargs = {
        'InstanceProfileArn': instance_profile_arn,
        'InstanceType': instance_type,
        'ServiceRoleArn': service_role_arn
    }
    
    if backup_retention_count is not None:
        kwargs['BackupRetentionCount'] = backup_retention_count
    if server_name is not None:
        kwargs['ServerName'] = server_name
        
    # Create the server
    original = opsworkscm.Server(title, **kwargs)
    
    # Convert to dict and back
    as_dict = original.to_dict()
    
    # Extract just the Properties part for from_dict
    props = as_dict.get('Properties', {})
    reconstructed = opsworkscm.Server.from_dict(title, props)
    
    # Check equality
    assert original.to_dict() == reconstructed.to_dict()


@given(title=st.text(min_size=1))
def test_title_validation(title):
    """Test that title validation works as documented"""
    # Title must be alphanumeric according to validate_title()
    is_valid = all(c.isalnum() for c in title) and len(title) > 0
    
    try:
        server = opsworkscm.Server(
            title,
            InstanceProfileArn='arn:aws:iam::123456789012:instance-profile/MyProfile',
            InstanceType='m5.large',
            ServiceRoleArn='arn:aws:iam::123456789012:role/MyRole'
        )
        # If we got here, title was accepted
        assert is_valid, f"Title '{title}' should have been rejected but was accepted"
    except ValueError as e:
        # Title was rejected
        assert not is_valid, f"Title '{title}' should have been accepted but was rejected: {e}"


@given(
    title1=alphanumeric_str,
    title2=alphanumeric_str,
    arn=st.text(min_size=1),
    instance_type=st.text(min_size=1)
)
def test_equality_hash_consistency(title1, title2, arn, instance_type):
    """Test that equal objects have equal hashes"""
    # Create two servers with same properties
    kwargs = {
        'InstanceProfileArn': arn,
        'InstanceType': instance_type,
        'ServiceRoleArn': arn
    }
    
    server1 = opsworkscm.Server(title1, **kwargs)
    server2 = opsworkscm.Server(title1, **kwargs)
    server3 = opsworkscm.Server(title2, **kwargs)
    
    # Same title and properties should be equal
    if title1 == title2:
        assert server1 == server3
        assert hash(server1) == hash(server3)
    
    # Same object should always be equal to itself
    assert server1 == server1
    assert hash(server1) == hash(server1)
    
    # Objects with same title and properties should be equal
    assert server1 == server2
    assert hash(server1) == hash(server2)


@given(
    instance_profile_arn=st.one_of(st.none(), st.text()),
    instance_type=st.one_of(st.none(), st.text()),
    service_role_arn=st.one_of(st.none(), st.text())
)
def test_required_properties_validation(instance_profile_arn, instance_type, service_role_arn):
    """Test that required properties are enforced"""
    kwargs = {}
    if instance_profile_arn is not None:
        kwargs['InstanceProfileArn'] = instance_profile_arn
    if instance_type is not None:
        kwargs['InstanceType'] = instance_type
    if service_role_arn is not None:
        kwargs['ServiceRoleArn'] = service_role_arn
    
    # All three are required
    all_present = all([
        instance_profile_arn is not None,
        instance_type is not None, 
        service_role_arn is not None
    ])
    
    try:
        server = opsworkscm.Server('TestServer', **kwargs)
        # Need to call to_dict() to trigger validation
        server.to_dict()
        assert all_present, "Should have raised ValueError for missing required properties"
    except ValueError as e:
        assert not all_present, f"Should not have raised ValueError when all required properties present: {e}"


@given(
    title=alphanumeric_str,
    tags_value=st.one_of(
        st.lists(st.builds(dict, Key=st.text(), Value=st.text())),
        st.builds(Tags, st.dictionaries(st.text(min_size=1), st.text())),
        st.text(),  # Invalid type
        st.integers(),  # Invalid type
        st.booleans()  # Invalid type
    )
)
def test_tags_validation(title, tags_value):
    """Test that Tags property validates correctly"""
    from troposphere import AWSHelperFn
    
    # Determine if the value should be valid
    is_valid = isinstance(tags_value, (list, Tags, AWSHelperFn))
    
    kwargs = {
        'InstanceProfileArn': 'arn',
        'InstanceType': 'type',
        'ServiceRoleArn': 'arn',
        'Tags': tags_value
    }
    
    try:
        server = opsworkscm.Server(title, **kwargs)
        # Accessing the Tags property might trigger validation
        _ = server.Tags
        if not is_valid:
            # Try to trigger validation through to_dict
            server.to_dict()
        assert is_valid, f"Tags value {tags_value} of type {type(tags_value)} should have been rejected"
    except (ValueError, TypeError) as e:
        assert not is_valid, f"Tags value should have been accepted but got: {e}"


if __name__ == '__main__':
    print("Running property-based tests for troposphere.opsworkscm...")
    
    # Run with more examples for thorough testing
    test_engine_attribute_roundtrip()
    test_server_roundtrip_with_required_fields()
    test_title_validation()
    test_equality_hash_consistency()
    test_required_properties_validation()
    test_tags_validation()
    
    print("All tests completed!")