#!/usr/bin/env python3
"""
Comprehensive bug hunting for troposphere.iotsitewise
Looking for actual bugs, not just expected behavior
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import re
import troposphere.iotsitewise as iotsitewise
from troposphere import Tags

print("Comprehensive Bug Hunt for troposphere.iotsitewise")
print("="*60)

# Bug Hunt 1: Title validation regex edge cases
print("\n1. Testing title validation edge cases...")
print("-"*40)

test_cases = [
    ("ValidTitle123", True, "alphanumeric"),
    ("", False, "empty string"),
    ("123", True, "numeric only"),
    ("Title_With_Underscore", False, "underscore"),
    ("Title-With-Dash", False, "dash"),
    ("Title With Space", False, "space"),
    ("TitleWithÜmlaut", False, "non-ASCII"),
    ("Title.With.Dot", False, "dot"),
    ("0StartWithNumber", True, "starts with number"),
    ("_StartWithUnderscore", False, "starts with underscore"),
]

bugs_found = []

for title, should_pass, description in test_cases:
    try:
        obj = iotsitewise.AccessPolicy(
            title,
            AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(),
            AccessPolicyPermission="VIEWER",
            AccessPolicyResource=iotsitewise.AccessPolicyResource()
        )
        if should_pass:
            print(f"  ✓ {description}: '{title}' accepted")
        else:
            print(f"  ✗ BUG: {description}: '{title}' should be rejected but was accepted")
            bugs_found.append(f"Title validation accepts '{title}' ({description})")
    except ValueError:
        if not should_pass:
            print(f"  ✓ {description}: '{title}' rejected")
        else:
            print(f"  ✗ BUG: {description}: '{title}' should be accepted but was rejected")
            bugs_found.append(f"Title validation rejects '{title}' ({description})")

# Bug Hunt 2: Property validation bypass
print("\n2. Testing property validation bypass...")
print("-"*40)

try:
    # Create an asset with wrong type
    asset = iotsitewise.Asset("TestAsset")
    # Try to set a list where string is expected
    asset.AssetName = ["Not", "A", "String"]
    print(f"  ✗ BUG: AssetName accepts list instead of string: {asset.AssetName}")
    bugs_found.append("AssetName property accepts list instead of string")
except (TypeError, AttributeError) as e:
    print(f"  ✓ Property type validation works: {e}")

# Bug Hunt 3: Required field validation timing
print("\n3. Testing required field validation timing...")
print("-"*40)

try:
    # Create object without required fields
    gateway = iotsitewise.Gateway("TestGateway")
    
    # Try to get JSON without validation
    json_str = gateway.to_json(validation=False)
    parsed = json.loads(json_str)
    
    # Check if the invalid template was created
    if "Properties" not in parsed or not parsed["Properties"]:
        print(f"  ✗ BUG: to_json(validation=False) creates template with empty Properties")
        bugs_found.append("to_json(validation=False) creates invalid CloudFormation template")
    else:
        print(f"  ✓ to_json(validation=False) includes Properties section")
        
except Exception as e:
    print(f"  Error during test: {e}")

# Bug Hunt 4: None value handling inconsistency
print("\n4. Testing None value handling...")
print("-"*40)

try:
    # Test with explicit None
    hierarchy = iotsitewise.AssetHierarchy(
        ChildAssetId="child-123",
        Id=None,
        ExternalId=None
    )
    
    dict_repr = hierarchy.to_dict()
    
    # Check if None values are in the dict
    none_count = sum(1 for v in dict_repr.values() if v is None)
    if none_count > 0:
        print(f"  ✗ BUG: to_dict() includes {none_count} None values in output")
        bugs_found.append(f"to_dict() includes None values in output dictionary")
    else:
        print(f"  ✓ None values are excluded from dict output")
        
except Exception as e:
    print(f"  Error during test: {e}")

# Bug Hunt 5: JSON encoding of special values
print("\n5. Testing JSON encoding of special values...")
print("-"*40)

special_values = [
    (float('inf'), "infinity"),
    (float('-inf'), "negative infinity"),
    (float('nan'), "NaN"),
]

for value, description in special_values:
    try:
        # Try to use special float as a string property (through string conversion)
        asset = iotsitewise.Asset(
            "TestAsset",
            AssetName=str(value),
            AssetModelId="model-123"
        )
        
        json_str = asset.to_json()
        parsed = json.loads(json_str)
        
        if parsed["Properties"]["AssetName"] != str(value):
            print(f"  ✗ BUG: {description} not preserved: got {parsed['Properties']['AssetName']}")
            bugs_found.append(f"JSON encoding changes {description} value")
        else:
            print(f"  ✓ {description} handled correctly as string")
            
    except (ValueError, OverflowError) as e:
        print(f"  ✓ {description} raises error: {e}")
    except Exception as e:
        print(f"  ? Unexpected error with {description}: {e}")

# Bug Hunt 6: Circular reference handling
print("\n6. Testing circular reference handling...")
print("-"*40)

try:
    # Create a potential circular reference through dict
    circular_dict = {}
    circular_dict['self'] = circular_dict
    
    portal = iotsitewise.Portal(
        "TestPortal",
        PortalName="Test",
        PortalContactEmail="test@example.com",
        RoleArn="arn:aws:iam::123456789012:role/MyRole",
        PortalTypeConfiguration=circular_dict
    )
    
    # This should fail when trying to serialize
    try:
        json_str = portal.to_json()
        print(f"  ✗ BUG: Circular reference in dict property doesn't raise error")
        bugs_found.append("Circular references in dict properties not detected")
    except (ValueError, RecursionError) as e:
        print(f"  ✓ Circular reference detected: {type(e).__name__}")
        
except Exception as e:
    print(f"  Error during test: {e}")

# Bug Hunt 7: Unicode handling in properties  
print("\n7. Testing Unicode handling...")
print("-"*40)

unicode_tests = [
    ("Hello 世界", "Chinese characters"),
    ("Emoji 🎉 test", "emoji"),
    ("Привет мир", "Cyrillic"),
    ("مرحبا بالعالم", "Arabic RTL"),
    ("\u0000null\u0000char", "null characters"),
    ("Line\nBreak", "line break"),
    ("Tab\tCharacter", "tab character"),
]

for text, description in unicode_tests:
    try:
        asset = iotsitewise.Asset(
            "TestAsset",
            AssetName=text,
            AssetModelId="model-123"
        )
        
        json_str = asset.to_json()
        parsed = json.loads(json_str)
        
        if parsed["Properties"]["AssetName"] != text:
            print(f"  ✗ BUG: {description} not preserved: '{text}' -> '{parsed['Properties']['AssetName']}'")
            bugs_found.append(f"Unicode handling issue with {description}")
        else:
            print(f"  ✓ {description} preserved correctly")
            
    except Exception as e:
        print(f"  ? Error with {description}: {e}")

# Bug Hunt 8: Tags handling
print("\n8. Testing Tags handling...")
print("-"*40)

try:
    # Test with Tags
    tags = Tags(
        Name="TestAsset",
        Environment="Production",
        CostCenter="Engineering"
    )
    
    asset = iotsitewise.Asset(
        "TestAsset",
        AssetName="Test",
        AssetModelId="model-123",
        Tags=tags
    )
    
    dict_repr = asset.to_dict()
    
    if "Tags" in dict_repr["Properties"]:
        tags_output = dict_repr["Properties"]["Tags"]
        print(f"  ✓ Tags included in output: {type(tags_output)}")
    else:
        print(f"  ✗ BUG: Tags not included in output")
        bugs_found.append("Tags property not included in to_dict output")
        
except Exception as e:
    print(f"  Error during test: {e}")

# Bug Hunt 9: Property name collision
print("\n9. Testing property name collision...")
print("-"*40)

try:
    # Try to set both a real property and a resource attribute
    policy = iotsitewise.AccessPolicy(
        "TestPolicy",
        AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(),
        AccessPolicyPermission="VIEWER",
        AccessPolicyResource=iotsitewise.AccessPolicyResource(),
        DependsOn=["SomeResource"],  # This is an attribute, not a property
        Metadata={"key": "value"}  # This is also an attribute
    )
    
    dict_repr = policy.to_dict()
    
    # Check if attributes are separated from properties
    if "DependsOn" in dict_repr and "DependsOn" not in dict_repr.get("Properties", {}):
        print(f"  ✓ Attributes correctly separated from Properties")
    else:
        print(f"  ✗ BUG: Attributes mixed with Properties")
        bugs_found.append("Resource attributes not properly separated from Properties")
        
except Exception as e:
    print(f"  Error during test: {e}")

# Summary
print("\n" + "="*60)
print(f"\nBug Hunt Complete!")
print(f"Found {len(bugs_found)} potential issues:\n")

if bugs_found:
    for i, bug in enumerate(bugs_found, 1):
        print(f"  {i}. {bug}")
else:
    print("  No bugs found - all tests passed!")

print("\nNote: Some behaviors may be by design for CloudFormation compatibility.")