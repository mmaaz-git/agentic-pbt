#!/usr/bin/env python3
"""Manual test to find bugs in troposphere.opsworkscm"""

import sys
import os

# Set up path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
os.chdir('/root/hypothesis-llm/worker_/3')

print("Manual Bug Testing for troposphere.opsworkscm")
print("=" * 60)

import troposphere.opsworkscm as opsworkscm

# Bug Test 1: Empty string round-trip
print("\nTest 1: Empty string handling in EngineAttribute")
print("-" * 40)

try:
    # Create with empty strings
    ea1 = opsworkscm.EngineAttribute(Name="", Value="")
    print(f"Created EngineAttribute with empty strings")
    
    # Convert to dict
    d1 = ea1.to_dict()
    print(f"to_dict() = {d1}")
    
    # Try to recreate from dict
    ea2 = opsworkscm.EngineAttribute.from_dict(None, d1)
    print(f"from_dict() succeeded")
    
    # Check equality
    are_equal = (ea1 == ea2)
    print(f"Original == Restored: {are_equal}")
    
    if not are_equal:
        print("*** POTENTIAL BUG: Round-trip failed! ***")
        print(f"Original.__dict__ = {ea1.__dict__}")
        print(f"Restored.__dict__ = {ea2.__dict__}")
        
        # Check individual properties
        print(f"Original.properties = {ea1.properties}")
        print(f"Restored.properties = {ea2.properties}")
        
except Exception as e:
    print(f"*** ERROR: {e} ***")
    import traceback
    traceback.print_exc()

# Bug Test 2: None vs not setting property
print("\nTest 2: None vs unset property in EngineAttribute")
print("-" * 40)

try:
    # Create without setting Name/Value
    ea_unset = opsworkscm.EngineAttribute()
    print(f"EngineAttribute() with no args")
    print(f"  to_dict() = {ea_unset.to_dict()}")
    print(f"  properties = {ea_unset.properties}")
    
    # Create with explicit None
    ea_none = opsworkscm.EngineAttribute(Name=None, Value=None)
    print(f"EngineAttribute(Name=None, Value=None)")
    print(f"  to_dict() = {ea_none.to_dict()}")  
    print(f"  properties = {ea_none.properties}")
    
    # Are they equal?
    print(f"unset == explicit_none: {ea_unset == ea_none}")
    
    # Round-trip test for unset
    d_unset = ea_unset.to_dict()
    ea_unset_restored = opsworkscm.EngineAttribute.from_dict(None, d_unset)
    print(f"Unset round-trip: {ea_unset == ea_unset_restored}")
    
except Exception as e:
    print(f"*** ERROR: {e} ***")
    import traceback
    traceback.print_exc()

# Bug Test 3: Hash consistency
print("\nTest 3: Hash consistency for equal objects")
print("-" * 40)

try:
    # Create two identical EngineAttributes
    ea1 = opsworkscm.EngineAttribute(Name="test", Value="value")
    ea2 = opsworkscm.EngineAttribute(Name="test", Value="value")
    
    print(f"Two identical EngineAttribute objects created")
    print(f"ea1 == ea2: {ea1 == ea2}")
    print(f"hash(ea1): {hash(ea1)}")
    print(f"hash(ea2): {hash(ea2)}")
    
    if ea1 == ea2:
        if hash(ea1) != hash(ea2):
            print("*** BUG FOUND: Equal objects have different hashes! ***")
        else:
            print("Hash consistency OK")
    
    # Test with Server objects
    s1 = opsworkscm.Server("S1", InstanceProfileArn="arn", InstanceType="t", ServiceRoleArn="r")
    s2 = opsworkscm.Server("S1", InstanceProfileArn="arn", InstanceType="t", ServiceRoleArn="r")
    
    print(f"\nTwo identical Server objects created")
    print(f"s1 == s2: {s1 == s2}")
    print(f"hash(s1): {hash(s1)}")
    print(f"hash(s2): {hash(s2)}")
    
    if s1 == s2:
        if hash(s1) != hash(s2):
            print("*** BUG FOUND: Equal Server objects have different hashes! ***")
        else:
            print("Hash consistency OK")
            
except Exception as e:
    print(f"*** ERROR: {e} ***")
    import traceback
    traceback.print_exc()

# Bug Test 4: Integer validator with string numbers
print("\nTest 4: Integer validator edge cases")
print("-" * 40)

test_values = [
    (0, "zero"),
    (1, "one"),
    ("0", "string zero"),
    ("1", "string one"),
    (1.0, "float 1.0"),
    (True, "boolean True"),
    (False, "boolean False"),
]

for val, desc in test_values:
    try:
        server = opsworkscm.Server(
            "Test",
            InstanceProfileArn="arn",
            InstanceType="type",
            ServiceRoleArn="role",
            BackupRetentionCount=val
        )
        server.to_dict()
        print(f"  {desc} ({repr(val)}): Accepted")
    except Exception as e:
        print(f"  {desc} ({repr(val)}): Rejected - {e}")

print("\n" + "=" * 60)
print("Manual testing complete!")