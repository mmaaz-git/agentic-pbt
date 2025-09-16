#!/usr/bin/env python3
import sys
import os

# Set the path to the troposphere package
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Now run a simple test
try:
    import troposphere.iotsitewise as iotsitewise
    
    # Test case 1: Create object with None title
    print("Testing creation with None title...")
    obj1 = iotsitewise.AccessPolicy(
        None,
        AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(),
        AccessPolicyPermission="VIEWER", 
        AccessPolicyResource=iotsitewise.AccessPolicyResource()
    )
    print(f"✓ Created with None title: {obj1.title}")
    
    # Test case 2: Create object with valid title
    print("\nTesting creation with valid title...")
    obj2 = iotsitewise.Asset(
        "MyAsset123",
        AssetName="Test Asset",
        AssetModelId="model-123"
    )
    dict_repr = obj2.to_dict()
    print(f"✓ Created asset, Type: {dict_repr.get('Type')}")
    print(f"  AssetName: {dict_repr['Properties']['AssetName']}")
    
    # Test case 3: Check missing required properties
    print("\nTesting missing required properties...")
    try:
        obj3 = iotsitewise.Asset("TestAsset")  # Missing required AssetName and AssetModelId
        dict3 = obj3.to_dict()
        print(f"WARNING: Created Asset without required properties!")
        print(f"  Dict: {dict3}")
    except Exception as e:
        print(f"✓ Correctly failed: {e}")
    
    print("\nBasic tests completed.")
    
except ImportError as e:
    print(f"Failed to import: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()