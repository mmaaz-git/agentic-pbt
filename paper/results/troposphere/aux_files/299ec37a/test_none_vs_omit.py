#!/usr/bin/env python3
"""Test the difference between omitting optional properties vs setting them to None."""
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

import troposphere.iotfleetwise as iotfleetwise

def test_optional_property_none_handling(cls_name, cls, required_props, optional_prop):
    """Test if a class handles None correctly for optional properties."""
    print(f"\nTesting {cls_name}:")
    
    # Test 1: Omitting the optional property
    try:
        obj1 = cls(title="Test1", **required_props)
        print(f"  ✓ Can create without {optional_prop}")
    except Exception as e:
        print(f"  ✗ Failed to create without {optional_prop}: {e}")
        return
    
    # Test 2: Explicitly setting optional property to None
    try:
        props_with_none = {**required_props, optional_prop: None}
        obj2 = cls(title="Test2", **props_with_none)
        print(f"  ✓ Can create with {optional_prop}=None")
    except Exception as e:
        print(f"  ✗ Failed to create with {optional_prop}=None: {e}")
        print(f"    This is a BUG - optional properties should accept None")
        return True  # Found a bug
    
    return False

# Test various classes
bugs_found = []

# Test StateTemplate
if test_optional_property_none_handling(
    "StateTemplate",
    iotfleetwise.StateTemplate,
    {
        "Name": "test",
        "SignalCatalogArn": "arn:test",
        "StateTemplateProperties": ["prop1"]
    },
    "Description"
):
    bugs_found.append("StateTemplate.Description")

# Test Campaign
if test_optional_property_none_handling(
    "Campaign", 
    iotfleetwise.Campaign,
    {
        "Name": "test",
        "SignalCatalogArn": "arn:test",
        "TargetArn": "arn:target",
        "CollectionScheme": iotfleetwise.CollectionScheme(
            TimeBasedCollectionScheme=iotfleetwise.TimeBasedCollectionScheme(PeriodMs=1000.0)
        )
    },
    "Description"
):
    bugs_found.append("Campaign.Description")

# Test Fleet
if test_optional_property_none_handling(
    "Fleet",
    iotfleetwise.Fleet,
    {
        "Id": "test-fleet",
        "SignalCatalogArn": "arn:test"
    },
    "Description"
):
    bugs_found.append("Fleet.Description")

# Test DecoderManifest
if test_optional_property_none_handling(
    "DecoderManifest",
    iotfleetwise.DecoderManifest,
    {
        "Name": "test-decoder",
        "ModelManifestArn": "arn:model"
    },
    "Description"
):
    bugs_found.append("DecoderManifest.Description")

# Test ModelManifest
if test_optional_property_none_handling(
    "ModelManifest",
    iotfleetwise.ModelManifest,
    {
        "Name": "test-model",
        "SignalCatalogArn": "arn:signal"
    },
    "Description"
):
    bugs_found.append("ModelManifest.Description")

# Test SignalCatalog
if test_optional_property_none_handling(
    "SignalCatalog",
    iotfleetwise.SignalCatalog,
    {},  # No required properties
    "Description"
):
    bugs_found.append("SignalCatalog.Description")

# Test Vehicle
if test_optional_property_none_handling(
    "Vehicle",
    iotfleetwise.Vehicle,
    {
        "Name": "test-vehicle",
        "DecoderManifestArn": "arn:decoder",
        "ModelManifestArn": "arn:model"
    },
    "AssociationBehavior"
):
    bugs_found.append("Vehicle.AssociationBehavior")

print(f"\n{'='*60}")
if bugs_found:
    print(f"BUGS FOUND in {len(bugs_found)} properties:")
    for bug in bugs_found:
        print(f"  - {bug}")
else:
    print("No bugs found - all optional properties handle None correctly")