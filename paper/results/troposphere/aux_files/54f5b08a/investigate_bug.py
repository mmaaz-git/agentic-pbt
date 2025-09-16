#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.panorama as panorama

print("=== Investigating the bug ===")

# Test 1: Numeric string as property name
print("\nTest 1: Property named '0'")
try:
    pkg = panorama.Package("TestPkg", PackageName="test", **{"0": "value"})
    print("Success - no error")
except AttributeError as e:
    print(f"AttributeError: {e}")

# Test 2: Other numeric strings
print("\nTest 2: Various numeric property names")
for prop_name in ["0", "1", "123", "00", "01"]:
    try:
        pkg = panorama.Package("TestPkg", PackageName="test", **{prop_name: "value"})
        print(f"  {prop_name}: Success")
    except AttributeError as e:
        print(f"  {prop_name}: AttributeError - {e}")

# Test 3: Property names that start with numbers
print("\nTest 3: Property names starting with numbers")
for prop_name in ["0abc", "1test", "123prop"]:
    try:
        pkg = panorama.Package("TestPkg", PackageName="test", **{prop_name: "value"})
        print(f"  {prop_name}: Success")
    except AttributeError as e:
        print(f"  {prop_name}: AttributeError - {e}")

# Test 4: Test with ApplicationInstance
print("\nTest 4: ApplicationInstance with numeric property")
try:
    app = panorama.ApplicationInstance(
        "TestApp",
        DefaultRuntimeContextDevice="device",
        ManifestPayload=panorama.ManifestPayload(PayloadData="data"),
        **{"0": "value"}
    )
    print("Success - no error")
except AttributeError as e:
    print(f"AttributeError: {e}")

# Test 5: Test other classes
print("\nTest 5: Other classes")
classes_to_test = [
    (panorama.ManifestPayload, {}),
    (panorama.StorageLocation, {}),
    (panorama.PackageVersion, {
        "PackageId": "id", 
        "PackageVersion": "1.0", 
        "PatchVersion": "1"
    })
]

for cls, required_props in classes_to_test:
    try:
        kwargs = required_props.copy()
        kwargs["0"] = "value"
        obj = cls("Test", **kwargs) if cls == panorama.PackageVersion else cls(**kwargs)
        print(f"  {cls.__name__}: Success")
    except AttributeError as e:
        print(f"  {cls.__name__}: AttributeError - {e}")

# Test 6: Check if this is a validation issue
print("\nTest 6: Is this a validation issue?")
try:
    # Try with validation disabled
    pkg = panorama.Package("TestPkg", validation=False, PackageName="test", **{"0": "value"})
    print("With validation=False: Still fails")
except AttributeError as e:
    print(f"With validation=False: AttributeError - {e}")