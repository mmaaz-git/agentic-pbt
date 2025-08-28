import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iotsitewise as iotsitewise
from troposphere import BaseAWSObject, AWSObject, AWSProperty, Tags
from hypothesis import given, strategies as st, assume, settings, seed
import json

# Test 1: Title validation with invalid characters
print("Test 1: Testing title validation with invalid characters...")
try:
    # This should fail because spaces are not alphanumeric
    obj = iotsitewise.AccessPolicy(
        "My Policy Name",  # Contains spaces - should be invalid
        AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(),
        AccessPolicyPermission="VIEWER",
        AccessPolicyResource=iotsitewise.AccessPolicyResource()
    )
    print("FAILED: Should have raised ValueError for non-alphanumeric title")
except ValueError as e:
    print(f"PASSED: Correctly rejected invalid title: {e}")

# Test 2: Title with special characters
print("\nTest 2: Testing title with special characters...")
try:
    obj = iotsitewise.AccessPolicy(
        "Policy-Name-123",  # Contains hyphens - should be invalid
        AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(),
        AccessPolicyPermission="VIEWER",
        AccessPolicyResource=iotsitewise.AccessPolicyResource()
    )
    print("FAILED: Should have raised ValueError for title with hyphens")
except ValueError as e:
    print(f"PASSED: Correctly rejected title with hyphens: {e}")

# Test 3: Valid alphanumeric title
print("\nTest 3: Testing valid alphanumeric title...")
try:
    obj = iotsitewise.AccessPolicy(
        "ValidPolicyName123",
        AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(),
        AccessPolicyPermission="VIEWER",
        AccessPolicyResource=iotsitewise.AccessPolicyResource()
    )
    print(f"PASSED: Accepted valid title: {obj.title}")
except ValueError as e:
    print(f"FAILED: Should have accepted alphanumeric title: {e}")

# Test 4: to_dict structure
print("\nTest 4: Testing to_dict structure...")
try:
    obj = iotsitewise.AccessPolicy(
        "TestPolicy",
        AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(
            IamRole=iotsitewise.IamRole(arn="arn:aws:iam::123456789012:role/MyRole"),
            User=iotsitewise.User(id="user-123")
        ),
        AccessPolicyPermission="ADMINISTRATOR",
        AccessPolicyResource=iotsitewise.AccessPolicyResource(
            Portal=iotsitewise.PortalProperty(id="portal-456")
        )
    )
    
    dict_repr = obj.to_dict()
    
    # Check structure
    assert "Type" in dict_repr
    assert dict_repr["Type"] == "AWS::IoTSiteWise::AccessPolicy"
    assert "Properties" in dict_repr
    
    props = dict_repr["Properties"]
    assert props["AccessPolicyPermission"] == "ADMINISTRATOR"
    assert props["AccessPolicyIdentity"]["IamRole"]["arn"] == "arn:aws:iam::123456789012:role/MyRole"
    assert props["AccessPolicyIdentity"]["User"]["id"] == "user-123"
    assert props["AccessPolicyResource"]["Portal"]["id"] == "portal-456"
    
    print("PASSED: to_dict produces correct structure")
except Exception as e:
    print(f"FAILED: {e}")

# Test 5: JSON serialization
print("\nTest 5: Testing JSON serialization...")
try:
    asset = iotsitewise.Asset(
        "TestAsset",
        AssetName="My Asset",
        AssetDescription="Test Description",
        AssetModelId="model-123"
    )
    
    json_str = asset.to_json()
    parsed = json.loads(json_str)
    
    assert parsed["Type"] == "AWS::IoTSiteWise::Asset"
    assert parsed["Properties"]["AssetName"] == "My Asset"
    assert parsed["Properties"]["AssetDescription"] == "Test Description"
    assert parsed["Properties"]["AssetModelId"] == "model-123"
    
    print("PASSED: JSON serialization works correctly")
except Exception as e:
    print(f"FAILED: {e}")

# Test 6: Empty title validation
print("\nTest 6: Testing empty title...")
try:
    obj = iotsitewise.AccessPolicy(
        "",  # Empty title
        AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(),
        AccessPolicyPermission="VIEWER",
        AccessPolicyResource=iotsitewise.AccessPolicyResource()
    )
    print("FAILED: Should have raised ValueError for empty title")
except ValueError as e:
    print(f"PASSED: Correctly rejected empty title: {e}")

# Test 7: None title - different behavior
print("\nTest 7: Testing None title...")
try:
    obj = iotsitewise.AccessPolicy(
        None,  # None title - should be allowed but won't validate
        AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(),
        AccessPolicyPermission="VIEWER",
        AccessPolicyResource=iotsitewise.AccessPolicyResource()
    )
    print(f"PASSED: None title is allowed (title={obj.title})")
except Exception as e:
    print(f"Error with None title: {e}")

# Test 8: Testing AssetHierarchy required field behavior
print("\nTest 8: Testing AssetHierarchy missing required field...")
try:
    # Try to create AssetHierarchy without required ChildAssetId
    hierarchy = iotsitewise.AssetHierarchy()
    dict_repr = hierarchy.to_dict()
    # Check if it validates required fields
    print(f"WARNING: AssetHierarchy created without required ChildAssetId: {dict_repr}")
except Exception as e:
    print(f"Correctly failed when missing required field: {e}")

# Test 9: Unicode in titles
print("\nTest 9: Testing Unicode characters in title...")
try:
    obj = iotsitewise.AccessPolicy(
        "Policy名前",  # Contains Japanese characters
        AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(),
        AccessPolicyPermission="VIEWER",
        AccessPolicyResource=iotsitewise.AccessPolicyResource()
    )
    print("FAILED: Should have raised ValueError for non-ASCII characters")
except ValueError as e:
    print(f"PASSED: Correctly rejected non-ASCII title: {e}")

# Test 10: Testing numeric-only title
print("\nTest 10: Testing numeric-only title...")
try:
    obj = iotsitewise.AccessPolicy(
        "12345",  # Only numbers
        AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(),
        AccessPolicyPermission="VIEWER",
        AccessPolicyResource=iotsitewise.AccessPolicyResource()
    )
    print(f"PASSED: Accepted numeric-only title: {obj.title}")
except ValueError as e:
    print(f"FAILED: Should accept numeric-only title: {e}")

print("\nAll manual tests completed!")