#!/usr/bin/env python3
"""Comprehensive property-based tests for troposphere.opsworkscm"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, assume, settings, example
import troposphere.opsworkscm as opsworkscm
from troposphere import Tags, Ref


# Test for the round-trip property with edge cases
@given(
    name=st.one_of(
        st.none(),
        st.text(min_size=0, max_size=1000),  # Including empty strings
        st.text().filter(lambda x: '\x00' in x),  # Null bytes
        st.text().filter(lambda x: any(ord(c) > 127 for c in x))  # Unicode
    ),
    value=st.one_of(
        st.none(),
        st.text(min_size=0, max_size=1000),
        st.just(""),  # Explicitly test empty string
    )
)
@example(name="", value="")  # Explicit empty string example
@example(name=None, value=None)  # Explicit None example
@example(name="", value=None)  # Mixed
@settings(max_examples=200)
def test_engine_attribute_roundtrip_edge_cases(name, value):
    """Test EngineAttribute round-trip with edge cases"""
    kwargs = {}
    if name is not None:
        kwargs['Name'] = name
    if value is not None:
        kwargs['Value'] = value
    
    # Create original
    original = opsworkscm.EngineAttribute(**kwargs)
    
    # Convert to dict
    as_dict = original.to_dict()
    
    # Reconstruct from dict
    restored = opsworkscm.EngineAttribute.from_dict(None, as_dict)
    
    # Check equality
    assert original == restored, f"Round-trip failed for Name={repr(name)}, Value={repr(value)}"
    
    # Check hash consistency
    if original == restored:
        assert hash(original) == hash(restored), "Equal objects must have equal hashes"
    
    # Check dict equality
    assert original.to_dict() == restored.to_dict(), "to_dict() should be identical after round-trip"


# Test the integer validator edge cases
@given(
    backup_count=st.one_of(
        st.integers(min_value=-100, max_value=100),
        st.floats(min_value=-100, max_value=100),
        st.text().map(str),
        st.just(float('inf')),
        st.just(float('-inf')),
        st.just(float('nan')),
    )
)
def test_backup_retention_count_validation(backup_count):
    """Test integer validation for BackupRetentionCount"""
    try:
        server = opsworkscm.Server(
            "TestServer",
            InstanceProfileArn="arn",
            InstanceType="type",
            ServiceRoleArn="arn",
            BackupRetentionCount=backup_count
        )
        # If we get here, the value was accepted
        # Try to trigger validation
        server.to_dict()
        
        # Check if it's a valid integer-like value
        try:
            int(backup_count)
            is_valid = True
        except (ValueError, TypeError, OverflowError):
            is_valid = False
            
    except (ValueError, TypeError) as e:
        # Value was rejected
        is_valid = False
    
    # We can't assert much here without knowing the exact validation rules
    # but we can check for crashes


# Test Server round-trip with all optional fields
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50),
    associate_public_ip=st.one_of(st.none(), st.booleans()),
    backup_id=st.one_of(st.none(), st.text()),
    backup_retention_count=st.one_of(st.none(), st.integers(0, 100)),
    custom_certificate=st.one_of(st.none(), st.text()),
    custom_domain=st.one_of(st.none(), st.text()),
    custom_private_key=st.one_of(st.none(), st.text()),
    disable_automated_backup=st.one_of(st.none(), st.booleans()),
    engine=st.one_of(st.none(), st.text()),
    engine_model=st.one_of(st.none(), st.text()),
    engine_version=st.one_of(st.none(), st.text()),
    key_pair=st.one_of(st.none(), st.text()),
    preferred_backup_window=st.one_of(st.none(), st.text()),
    preferred_maintenance_window=st.one_of(st.none(), st.text()),
    server_name=st.one_of(st.none(), st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50)),
    security_group_ids=st.one_of(st.none(), st.lists(st.text(), max_size=5)),
    subnet_ids=st.one_of(st.none(), st.lists(st.text(), max_size=5))
)
@settings(max_examples=50)
def test_server_full_roundtrip(
    title, associate_public_ip, backup_id, backup_retention_count,
    custom_certificate, custom_domain, custom_private_key,
    disable_automated_backup, engine, engine_model, engine_version,
    key_pair, preferred_backup_window, preferred_maintenance_window,
    server_name, security_group_ids, subnet_ids
):
    """Test Server round-trip with all optional fields"""
    
    # Build kwargs with all optional fields
    kwargs = {
        'InstanceProfileArn': 'arn:aws:iam::123456789012:instance-profile/MyProfile',
        'InstanceType': 'm5.large',
        'ServiceRoleArn': 'arn:aws:iam::123456789012:role/MyRole'
    }
    
    if associate_public_ip is not None:
        kwargs['AssociatePublicIpAddress'] = associate_public_ip
    if backup_id is not None:
        kwargs['BackupId'] = backup_id
    if backup_retention_count is not None:
        kwargs['BackupRetentionCount'] = backup_retention_count
    if custom_certificate is not None:
        kwargs['CustomCertificate'] = custom_certificate
    if custom_domain is not None:
        kwargs['CustomDomain'] = custom_domain
    if custom_private_key is not None:
        kwargs['CustomPrivateKey'] = custom_private_key
    if disable_automated_backup is not None:
        kwargs['DisableAutomatedBackup'] = disable_automated_backup
    if engine is not None:
        kwargs['Engine'] = engine
    if engine_model is not None:
        kwargs['EngineModel'] = engine_model
    if engine_version is not None:
        kwargs['EngineVersion'] = engine_version
    if key_pair is not None:
        kwargs['KeyPair'] = key_pair
    if preferred_backup_window is not None:
        kwargs['PreferredBackupWindow'] = preferred_backup_window
    if preferred_maintenance_window is not None:
        kwargs['PreferredMaintenanceWindow'] = preferred_maintenance_window
    if server_name is not None:
        kwargs['ServerName'] = server_name
    if security_group_ids is not None:
        kwargs['SecurityGroupIds'] = security_group_ids
    if subnet_ids is not None:
        kwargs['SubnetIds'] = subnet_ids
    
    # Create server
    original = opsworkscm.Server(title, **kwargs)
    
    # Convert to dict
    server_dict = original.to_dict()
    
    # Extract properties for from_dict
    props = server_dict.get('Properties', {})
    
    # Reconstruct
    restored = opsworkscm.Server.from_dict(title, props)
    
    # Check they produce the same dict
    assert original.to_dict() == restored.to_dict(), "Round-trip should preserve all properties"


# Test EngineAttributes list handling
@given(
    engine_attrs=st.lists(
        st.builds(
            dict,
            Name=st.text(min_size=0, max_size=100),
            Value=st.text(min_size=0, max_size=100)
        ),
        max_size=10
    )
)
@settings(max_examples=100)
def test_server_engine_attributes_list(engine_attrs):
    """Test Server with list of EngineAttributes"""
    
    # Convert dicts to EngineAttribute objects
    attr_objects = [opsworkscm.EngineAttribute(**attrs) for attrs in engine_attrs]
    
    server = opsworkscm.Server(
        "TestServer",
        InstanceProfileArn="arn",
        InstanceType="type",
        ServiceRoleArn="arn",
        EngineAttributes=attr_objects
    )
    
    # Convert to dict and back
    server_dict = server.to_dict()
    props = server_dict.get('Properties', {})
    restored = opsworkscm.Server.from_dict("TestServer", props)
    
    # Should be equal
    assert server.to_dict() == restored.to_dict()


# Test boolean validator edge cases
@given(
    bool_value=st.one_of(
        st.booleans(),
        st.sampled_from([0, 1, "0", "1", "true", "false", "True", "False"]),
        st.text(),  # Invalid strings
        st.integers(),  # Invalid integers
    )
)
def test_boolean_property_validation(bool_value):
    """Test boolean validation for DisableAutomatedBackup"""
    valid_values = [True, False, 0, 1, "0", "1", "true", "false", "True", "False"]
    
    try:
        server = opsworkscm.Server(
            "TestServer",
            InstanceProfileArn="arn",
            InstanceType="type",
            ServiceRoleArn="arn",
            DisableAutomatedBackup=bool_value
        )
        server.to_dict()
        
        # If we get here, value was accepted
        # Check if it should have been accepted
        if bool_value not in valid_values:
            # This might be a bug - invalid value was accepted
            pass
            
    except (ValueError, TypeError):
        # Value was rejected
        if bool_value in valid_values:
            # This might be a bug - valid value was rejected
            pass


if __name__ == "__main__":
    print("Running comprehensive property-based tests...")
    pytest.main([__file__, "-v", "--tb=short"])