#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.panorama as panorama
import json

# Test creating objects with valid properties
print("=== Testing ApplicationInstance ===")
manifest = panorama.ManifestPayload(PayloadData="test-payload")
app = panorama.ApplicationInstance(
    "TestApp",
    DefaultRuntimeContextDevice="test-device",
    ManifestPayload=manifest
)
print(f"Created ApplicationInstance: {app}")
print(f"to_dict result: {json.dumps(app.to_dict(), indent=2)}")

# Test from_dict
print("\n=== Testing from_dict ===")
dict_data = {
    "DefaultRuntimeContextDevice": "device-1",
    "ManifestPayload": {"PayloadData": "data-1"}
}
app2 = panorama.ApplicationInstance.from_dict("TestApp2", dict_data)
print(f"Created from dict: {app2}")
print(f"to_dict result: {json.dumps(app2.to_dict(), indent=2)}")

# Test Package
print("\n=== Testing Package ===")
pkg = panorama.Package("TestPackage", PackageName="my-package")
print(f"Created Package: {pkg}")
print(f"to_dict result: {json.dumps(pkg.to_dict(), indent=2)}")

# Test PackageVersion with boolean property
print("\n=== Testing PackageVersion ===")
pkgv = panorama.PackageVersion(
    "TestVersion",
    PackageId="pkg-123",
    PackageVersion="1.0.0",
    PatchVersion="1",
    MarkLatest=True
)
print(f"Created PackageVersion: {pkgv}")
print(f"to_dict result: {json.dumps(pkgv.to_dict(), indent=2)}")

# Test boolean validator
print("\n=== Testing boolean validator ===")
from troposphere.validators import boolean
test_values = [True, False, 1, 0, "true", "false", "True", "False", "1", "0"]
for val in test_values:
    result = boolean(val)
    print(f"boolean({repr(val)}) = {result}")

# Test invalid boolean
try:
    boolean("invalid")
except ValueError as e:
    print(f"boolean('invalid') raised ValueError as expected")

# Test Tags
print("\n=== Testing Tags ===")
from troposphere import Tags
tags = Tags({"Key1": "Value1", "Key2": "Value2"})
print(f"Tags: {tags}")
print(f"Tags.to_dict(): {tags.to_dict()}")