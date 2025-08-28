"""Reproduce the empty title validation bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.kms as kms

# The bug: Empty titles bypass validation
print("Testing empty title bug:")
print("-" * 40)

# Create a Key with empty title - should fail but doesn't
try:
    key = kms.Key('')
    print("✗ BUG CONFIRMED: Created Key with empty title")
    print(f"  key.title = {repr(key.title)}")
    
    # Try to convert to dict (which normally triggers validation)
    key_dict = key.to_dict()
    print(f"  Successfully converted to dict")
    print(f"  Dict output: {key_dict}")
    
except ValueError as e:
    print(f"✓ Correctly rejected empty title: {e}")

print()

# Same bug affects Alias
try:
    alias = kms.Alias('', AliasName="alias/test", TargetKeyId="key-123")
    print("✗ BUG CONFIRMED: Created Alias with empty title")
    print(f"  alias.title = {repr(alias.title)}")
    
    alias_dict = alias.to_dict()
    print(f"  Successfully converted to dict")
    
except ValueError as e:
    print(f"✓ Correctly rejected empty title: {e}")

print()

# Same bug affects ReplicaKey
try:
    replica = kms.ReplicaKey('', 
                            KeyPolicy={'Version': '2012-10-17'},
                            PrimaryKeyArn='arn:aws:kms:us-east-1:123456789012:key/12345678')
    print("✗ BUG CONFIRMED: Created ReplicaKey with empty title")
    print(f"  replica.title = {repr(replica.title)}")
    
    replica_dict = replica.to_dict()
    print(f"  Successfully converted to dict")
    
except ValueError as e:
    print(f"✓ Correctly rejected empty title: {e}")

print()
print("Bug Impact:")
print("-" * 40)
print("Empty titles bypass validation in all AWS resource types.")
print("This could cause issues when resources are referenced in templates.")
print("CloudFormation requires non-empty logical IDs for resources.")