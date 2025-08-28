#!/usr/bin/env python3
"""Confirm the round-trip bug affects all AWSObject classes"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import managedblockchain

def test_roundtrip(cls, title, **kwargs):
    """Test round-trip for a given class"""
    print(f"\nTesting {cls.__name__}")
    
    # Create object
    obj = cls(title, **kwargs)
    
    # Convert to dict
    dict_repr = obj.to_dict()
    print(f"  to_dict() returns: {list(dict_repr.keys())}")
    
    # Try from_dict with full dict (will fail for AWSObject)
    try:
        reconstructed = cls.from_dict(title, dict_repr)
        print(f"  from_dict(dict_repr) - SUCCESS")
    except AttributeError as e:
        print(f"  from_dict(dict_repr) - FAILED: {e}")
        
        # Try workaround if Properties key exists
        if 'Properties' in dict_repr:
            try:
                reconstructed = cls.from_dict(title, dict_repr['Properties'])
                print(f"  from_dict(dict_repr['Properties']) - SUCCESS (workaround)")
            except Exception as e2:
                print(f"  from_dict(dict_repr['Properties']) - FAILED: {e2}")

# Test AWSObject classes (have 'Type' and 'Properties' in dict)
test_roundtrip(managedblockchain.Accessor, 'TestAccessor', AccessorType='BILLING_TOKEN')
test_roundtrip(managedblockchain.Member, 'TestMember', 
               MemberConfiguration=managedblockchain.MemberConfiguration(Name='Test'))
test_roundtrip(managedblockchain.Node, 'TestNode', NetworkId='test-network',
               NodeConfiguration=managedblockchain.NodeConfiguration(
                   AvailabilityZone='us-east-1a', 
                   InstanceType='bc.t3.small'))

# Test AWSProperty classes (no 'Type', direct properties)
print("\n--- Testing AWSProperty classes (these should work) ---")
fabric_config = managedblockchain.MemberFabricConfiguration(
    AdminUsername='admin', 
    AdminPassword='password')
dict_repr = fabric_config.to_dict()
print(f"\nMemberFabricConfiguration.to_dict(): {dict_repr}")
reconstructed = managedblockchain.MemberFabricConfiguration.from_dict(None, dict_repr)
print(f"MemberFabricConfiguration round-trip: SUCCESS")