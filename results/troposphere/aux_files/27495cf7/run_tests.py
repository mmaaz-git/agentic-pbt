#!/usr/bin/env python3
"""Simple test runner for property-based tests"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, Verbosity
import troposphere.opsworkscm as opsworkscm
from troposphere import Tags

print("Starting property-based testing of troposphere.opsworkscm...")
print("=" * 60)

# Test 1: Round-trip property for EngineAttribute
print("\n1. Testing EngineAttribute round-trip property...")
try:
    @given(
        name=st.one_of(st.none(), st.text(min_size=0, max_size=100)),
        value=st.one_of(st.none(), st.text(min_size=0, max_size=100))
    )
    @settings(max_examples=100, verbosity=Verbosity.verbose)
    def test_engine_attribute_roundtrip(name, value):
        kwargs = {}
        if name is not None:
            kwargs['Name'] = name
        if value is not None:
            kwargs['Value'] = value
        
        original = opsworkscm.EngineAttribute(**kwargs)
        as_dict = original.to_dict()
        reconstructed = opsworkscm.EngineAttribute.from_dict(None, as_dict)
        
        assert original == reconstructed
        assert original.to_dict() == reconstructed.to_dict()
    
    test_engine_attribute_roundtrip()
    print("✓ EngineAttribute round-trip test PASSED")
except Exception as e:
    print(f"✗ EngineAttribute round-trip test FAILED: {e}")

# Test 2: Title validation
print("\n2. Testing title validation...")
try:
    @given(title=st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_title_validation(title):
        is_valid = all(c.isalnum() for c in title) and len(title) > 0
        
        try:
            server = opsworkscm.Server(
                title,
                InstanceProfileArn='arn:aws:iam::123456789012:instance-profile/MyProfile',
                InstanceType='m5.large',
                ServiceRoleArn='arn:aws:iam::123456789012:role/MyRole'
            )
            assert is_valid, f"Title '{title}' should have been rejected"
        except ValueError:
            assert not is_valid, f"Title '{title}' should have been accepted"
    
    test_title_validation()
    print("✓ Title validation test PASSED")
except Exception as e:
    print(f"✗ Title validation test FAILED: {e}")

# Test 3: Equality and hash consistency
print("\n3. Testing equality and hash consistency...")
try:
    @given(
        title1=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20),
        title2=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20),
    )
    @settings(max_examples=50)
    def test_equality_hash(title1, title2):
        kwargs = {
            'InstanceProfileArn': 'arn',
            'InstanceType': 'type',
            'ServiceRoleArn': 'arn'
        }
        
        server1 = opsworkscm.Server(title1, **kwargs)
        server2 = opsworkscm.Server(title1, **kwargs)
        
        # Same object properties should be equal
        assert server1 == server2
        assert hash(server1) == hash(server2)
    
    test_equality_hash()
    print("✓ Equality and hash consistency test PASSED")
except Exception as e:
    print(f"✗ Equality and hash consistency test FAILED: {e}")

# Test 4: Required properties validation
print("\n4. Testing required properties validation...")
try:
    @given(
        has_profile=st.booleans(),
        has_type=st.booleans(),
        has_role=st.booleans()
    )
    @settings(max_examples=8)  # Only 8 combinations
    def test_required_props(has_profile, has_type, has_role):
        kwargs = {}
        if has_profile:
            kwargs['InstanceProfileArn'] = 'arn'
        if has_type:
            kwargs['InstanceType'] = 'type'
        if has_role:
            kwargs['ServiceRoleArn'] = 'arn'
        
        all_present = has_profile and has_type and has_role
        
        try:
            server = opsworkscm.Server('TestServer', **kwargs)
            server.to_dict()  # Trigger validation
            assert all_present, "Should have raised ValueError"
        except ValueError:
            assert not all_present, "Should not have raised ValueError"
    
    test_required_props()
    print("✓ Required properties validation test PASSED")
except Exception as e:
    print(f"✗ Required properties validation test FAILED: {e}")

print("\n" + "=" * 60)
print("Testing complete!")