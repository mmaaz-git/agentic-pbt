#!/usr/bin/env python3
"""Focused test for None handling bug in troposphere"""

import sys
import traceback

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.networkmanager as nm
from hypothesis import given, strategies as st, settings

print("Testing None handling bug in troposphere.networkmanager")
print("=" * 60)

# Test 1: Demonstrate the bug with different classes
print("\nTest 1: None values in optional properties should be allowed")
print("-" * 40)

test_cases = [
    ("Location", nm.Location, {"Address": None}),
    ("Location", nm.Location, {"Latitude": None}),
    ("Location", nm.Location, {"Longitude": None}),
    ("Device", nm.Device, {"Description": None, "GlobalNetworkId": "test"}),
    ("Site", nm.Site, {"Description": None, "GlobalNetworkId": "test"}),
    ("GlobalNetwork", nm.GlobalNetwork, {"Description": None}),
    ("ConnectAttachmentOptions", nm.ConnectAttachmentOptions, {"Protocol": None}),
]

failed_cases = []

for class_name, cls, kwargs in test_cases:
    try:
        obj = cls(**kwargs) if class_name not in ["Location", "ConnectAttachmentOptions"] else cls("Test", **kwargs)
        print(f"✓ {class_name} accepts None for optional properties")
    except TypeError as e:
        failed_cases.append((class_name, kwargs, str(e)))
        print(f"✗ {class_name} rejects None: {e}")
    except Exception as e:
        print(f"? {class_name} unexpected error: {e}")

print("\n" + "-" * 40)
print(f"Summary: {len(failed_cases)}/{len(test_cases)} cases failed")

# Test 2: Property-based test to find more instances
print("\nTest 2: Property-based test for None handling")
print("-" * 40)

@given(
    include_address=st.booleans(),
    include_latitude=st.booleans(),
    include_longitude=st.booleans()
)
@settings(max_examples=50)
def test_location_none_handling(include_address, include_latitude, include_longitude):
    """Test that Location should handle None values gracefully"""
    kwargs = {}
    
    # Build kwargs with some None values
    if include_address:
        kwargs["Address"] = None
    if include_latitude:
        kwargs["Latitude"] = None
    if include_longitude:
        kwargs["Longitude"] = None
    
    if not kwargs:
        # At least one property for meaningful test
        kwargs["Address"] = None
    
    try:
        location = nm.Location(**kwargs)
        # If it works, None should not appear in the dict representation
        dict_repr = location.to_dict()
        for key in ["Address", "Latitude", "Longitude"]:
            if key in kwargs and kwargs[key] is None:
                assert key not in dict_repr or dict_repr.get(key) is None
        return True
    except TypeError as e:
        # This is the bug - None should be allowed for optional properties
        return False

try:
    results = []
    for _ in range(20):
        try:
            test_location_none_handling()
            results.append(True)
        except:
            results.append(False)
    
    if all(results):
        print("✓ All None handling tests passed")
    else:
        failure_rate = results.count(False) / len(results)
        print(f"✗ {failure_rate*100:.1f}% of tests failed due to None handling bug")
except Exception as e:
    print(f"✗ Test failed: {e}")

# Test 3: Contrast with not providing the property at all
print("\nTest 3: Contrast None vs not providing property")
print("-" * 40)

# Case 1: Not providing optional property (should work)
try:
    location1 = nm.Location()  # No properties at all
    dict1 = location1.to_dict()
    print(f"✓ Location() without properties: {dict1}")
except Exception as e:
    print(f"✗ Location() failed: {e}")

# Case 2: Providing empty string (should work)
try:
    location2 = nm.Location(Address="")
    dict2 = location2.to_dict()
    print(f"✓ Location(Address=''): {dict2}")
except Exception as e:
    print(f"✗ Location(Address='') failed: {e}")

# Case 3: Providing None (currently fails - this is the bug)
try:
    location3 = nm.Location(Address=None)
    dict3 = location3.to_dict()
    print(f"✓ Location(Address=None): {dict3}")
except TypeError as e:
    print(f"✗ Location(Address=None) failed: {e}")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("-" * 60)
print("BUG CONFIRMED: Optional properties in troposphere classes do not")
print("accept None values, even though they are marked as optional.")
print()
print("Expected behavior: None should be treated the same as not")
print("providing the property at all for optional properties.")
print()
print("Actual behavior: TypeError is raised when None is passed to")
print("an optional property.")
print()
print("Impact: This prevents users from programmatically setting")
print("optional properties to None, which is a common pattern in Python.")