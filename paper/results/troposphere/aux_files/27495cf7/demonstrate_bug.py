#!/usr/bin/env python3
"""Demonstrate potential bug in troposphere.opsworkscm"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

print("Attempting to demonstrate potential bugs in troposphere.opsworkscm...")
print("=" * 70)

try:
    import troposphere.opsworkscm as opsworkscm
    
    # Bug Hunt 1: Round-trip property
    print("\n1. Testing round-trip property (to_dict -> from_dict)...")
    print("-" * 50)
    
    # Create an EngineAttribute with empty string values
    ea_original = opsworkscm.EngineAttribute(Name="", Value="")
    print(f"Original EngineAttribute created with Name='', Value=''")
    
    # Convert to dict
    ea_dict = ea_original.to_dict()
    print(f"to_dict() result: {ea_dict}")
    
    # Try to reconstruct from dict
    try:
        ea_restored = opsworkscm.EngineAttribute.from_dict(None, ea_dict)
        print(f"from_dict() succeeded")
        
        # Check if they're equal
        are_equal = (ea_original == ea_restored)
        print(f"original == restored: {are_equal}")
        
        if not are_equal:
            print("BUG FOUND: Round-trip failed to preserve equality!")
            print(f"Original to_dict: {ea_original.to_dict()}")
            print(f"Restored to_dict: {ea_restored.to_dict()}")
    except Exception as e:
        print(f"from_dict() failed: {e}")
        print("BUG FOUND: from_dict() cannot handle output of to_dict()!")
    
    # Bug Hunt 2: Hash/Equality consistency
    print("\n2. Testing hash/equality consistency...")
    print("-" * 50)
    
    # Create two identical EngineAttributes
    ea1 = opsworkscm.EngineAttribute(Name="test", Value="value")
    ea2 = opsworkscm.EngineAttribute(Name="test", Value="value")
    
    eq_result = (ea1 == ea2)
    hash1 = hash(ea1)
    hash2 = hash(ea2)
    
    print(f"ea1 == ea2: {eq_result}")
    print(f"hash(ea1): {hash1}")
    print(f"hash(ea2): {hash2}")
    print(f"hash(ea1) == hash(ea2): {hash1 == hash2}")
    
    if eq_result and hash1 != hash2:
        print("BUG FOUND: Equal objects have different hashes!")
    
    # Bug Hunt 3: Empty vs None in round-trip
    print("\n3. Testing empty string vs None in properties...")
    print("-" * 50)
    
    # Create EngineAttribute with no arguments
    ea_none = opsworkscm.EngineAttribute()
    print(f"EngineAttribute() with no args - to_dict: {ea_none.to_dict()}")
    
    # Create with empty strings
    ea_empty = opsworkscm.EngineAttribute(Name="", Value="")
    print(f"EngineAttribute(Name='', Value='') - to_dict: {ea_empty.to_dict()}")
    
    # Are they equal?
    print(f"no_args == empty_strings: {ea_none == ea_empty}")
    
    # Bug Hunt 4: Server with special characters in property values
    print("\n4. Testing Server with special characters...")
    print("-" * 50)
    
    # Try creating a server with Unicode in ARN
    try:
        server = opsworkscm.Server(
            "TestServer",
            InstanceProfileArn="arn:aws:iam::123456789012:instance-profile/Test\u2764",  # Unicode heart
            InstanceType="m5.large",
            ServiceRoleArn="arn:aws:iam::123456789012:role/MyRole"
        )
        server_dict = server.to_dict()
        print(f"Server with Unicode created successfully")
        
        # Try round-trip
        props = server_dict.get('Properties', {})
        server_restored = opsworkscm.Server.from_dict("TestServer", props)
        
        print(f"Round-trip successful: {server == server_restored}")
        
    except Exception as e:
        print(f"Failed with special characters: {e}")
    
    # Bug Hunt 5: Integer values for BackupRetentionCount
    print("\n5. Testing integer property handling...")
    print("-" * 50)
    
    # The BackupRetentionCount uses integer validator - test edge cases
    test_values = [0, -1, "0", "1", 1.0, 1.5, float('inf')]
    
    for val in test_values:
        try:
            server = opsworkscm.Server(
                "TestServer",
                InstanceProfileArn="arn",
                InstanceType="type",
                ServiceRoleArn="arn",
                BackupRetentionCount=val
            )
            server.to_dict()  # Trigger validation
            print(f"BackupRetentionCount={repr(val)} - Accepted")
        except Exception as e:
            print(f"BackupRetentionCount={repr(val)} - Rejected: {e}")

    print("\n" + "=" * 70)
    print("Bug hunting complete!")
    
except Exception as e:
    print(f"Unexpected error during testing: {e}")
    import traceback
    traceback.print_exc()