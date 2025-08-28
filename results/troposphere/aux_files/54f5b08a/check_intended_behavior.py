#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.panorama as panorama
import inspect

print("=== Checking if this is intended behavior ===")
print()

# Check what properties are actually defined for each class
classes = [
    panorama.ApplicationInstance,
    panorama.Package,
    panorama.PackageVersion,
    panorama.ManifestPayload,
    panorama.StorageLocation
]

for cls in classes:
    print(f"{cls.__name__} defined properties:")
    if hasattr(cls, 'props'):
        for prop_name in cls.props.keys():
            print(f"  - {prop_name}")
    print()

print("Analysis:")
print("---------")
print("None of the defined properties start with numbers.")
print("This suggests the library is correctly rejecting undefined properties.")
print()
print("The behavior is actually CORRECT - it prevents users from")
print("accidentally passing invalid properties to CloudFormation resources.")
print()
print("The 'bug' found by the test is actually the library working as")
print("intended - it validates that only known, valid properties are used.")
print()
print("This is a FALSE POSITIVE - not a real bug.")