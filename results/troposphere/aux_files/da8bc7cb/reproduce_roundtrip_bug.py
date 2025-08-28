#!/usr/bin/env python3
"""Minimal reproduction of the round-trip bug in troposphere.managedblockchain"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import managedblockchain

# Create an Accessor object
accessor = managedblockchain.Accessor('TestAccessor', AccessorType='BILLING_TOKEN')

# Convert to dict
dict_repr = accessor.to_dict()
print("Dict representation:", dict_repr)

# Try to reconstruct from dict - this will fail
try:
    reconstructed = managedblockchain.Accessor.from_dict('TestAccessor', dict_repr)
    print("Successfully reconstructed")
except AttributeError as e:
    print(f"Error: {e}")
    print("\nThe issue is that to_dict() returns: {'Properties': {...}}")
    print("But from_dict() expects just the properties without the 'Properties' wrapper")
    
    # The correct way would be to pass just the Properties dict
    if 'Properties' in dict_repr:
        reconstructed = managedblockchain.Accessor.from_dict('TestAccessor', dict_repr['Properties'])
        print("\nWorkaround successful: passing dict_repr['Properties'] instead of dict_repr")
        print("Reconstructed accessor:", reconstructed.to_dict())