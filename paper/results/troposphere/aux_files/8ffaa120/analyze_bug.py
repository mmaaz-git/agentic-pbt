#!/usr/bin/env python3
"""
Analyzing potential bug in troposphere.iotsitewise

Based on code analysis:
1. The _validate_props method checks for required properties
2. But this validation only happens when to_dict() is called with validation=True
3. Objects can be created without required properties
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iotsitewise as iotsitewise

print("Bug Analysis: Missing Required Properties Validation\n")
print("="*60)

print("\nTest 1: Create Asset without required properties")
print("-" * 40)
try:
    # Asset requires AssetName and AssetModelId
    asset = iotsitewise.Asset("TestAsset")
    print("✓ Asset created without required properties")
    print(f"  Title: {asset.title}")
    print(f"  Properties dict: {asset.properties}")
    
    # Now try to convert to dict - this should trigger validation
    print("\n  Attempting to_dict()...")
    try:
        dict_repr = asset.to_dict()
        print(f"  ERROR: to_dict() succeeded when it should have failed!")
        print(f"  Dict: {dict_repr}")
    except ValueError as e:
        print(f"  ✓ to_dict() correctly failed: {e}")
        
    # Try with validation=False
    print("\n  Attempting to_dict(validation=False)...")
    dict_repr = asset.to_dict(validation=False)
    print(f"  ✓ to_dict(validation=False) succeeded")
    print(f"  Dict: {dict_repr}")
    
except Exception as e:
    print(f"✗ Unexpected error: {e}")

print("\n" + "="*60)
print("\nTest 2: Create AccessPolicy without required properties")
print("-" * 40)
try:
    # AccessPolicy requires AccessPolicyIdentity, AccessPolicyPermission, AccessPolicyResource
    policy = iotsitewise.AccessPolicy("TestPolicy")
    print("✓ AccessPolicy created without required properties")
    
    print("\n  Attempting to_dict()...")
    try:
        dict_repr = policy.to_dict()
        print(f"  ERROR: to_dict() succeeded when it should have failed!")
    except ValueError as e:
        print(f"  ✓ to_dict() correctly failed: {e}")
        
except Exception as e:
    print(f"✗ Unexpected error: {e}")

print("\n" + "="*60)
print("\nTest 3: Create Gateway without required properties")
print("-" * 40)
try:
    # Gateway requires GatewayName and GatewayPlatform
    gateway = iotsitewise.Gateway("TestGateway")
    print("✓ Gateway created without required properties")
    
    print("\n  Attempting to_json()...")
    try:
        json_str = gateway.to_json()
        print(f"  ERROR: to_json() succeeded when it should have failed!")
    except ValueError as e:
        print(f"  ✓ to_json() correctly failed: {e}")
        
    print("\n  Attempting to_json(validation=False)...")
    json_str = gateway.to_json(validation=False)
    print(f"  ✓ to_json(validation=False) succeeded")
    print(f"  JSON length: {len(json_str)} chars")
    
except Exception as e:
    print(f"✗ Unexpected error: {e}")

print("\n" + "="*60)
print("\nTest 4: Property type validation")
print("-" * 40)
try:
    # Try to set wrong type for a property
    asset = iotsitewise.Asset(
        "TestAsset",
        AssetName=12345,  # Should be string
        AssetModelId="model-123"
    )
    print("✓ Asset created with wrong type (int instead of str)")
    
    # Check what was stored
    print(f"  AssetName type: {type(asset.AssetName)}")
    print(f"  AssetName value: {asset.AssetName}")
    
    # Try to convert to dict
    print("\n  Attempting to_dict()...")
    dict_repr = asset.to_dict()
    print(f"  ✓ to_dict() succeeded")
    print(f"  AssetName in dict: {dict_repr['Properties']['AssetName']}")
    
except TypeError as e:
    print(f"  ✓ Correctly rejected wrong type: {e}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")

print("\n" + "="*60)
print("\nSummary:")
print("-" * 40)
print("""
The troposphere library allows:
1. Creating resource objects without required properties
2. Validation only occurs when calling to_dict() or to_json()
3. Validation can be bypassed with validation=False parameter
4. Type checking happens at property assignment time

This is likely by design to allow:
- Partial object construction
- Template composition
- Conditional property setting

However, this could lead to runtime errors if objects are serialized
without validation, potentially creating invalid CloudFormation templates.
""")