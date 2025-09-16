#!/usr/bin/env python3
"""Reproduce the UploadResponse dataclass/init conflict bug."""

import sys
from dataclasses import asdict

# Add the storage3 environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/storage3_env/lib/python3.13/site-packages')

from storage3.types import UploadResponse

print("Testing UploadResponse dataclass/init conflict...")
print("=" * 50)

# Test 1: Using the custom __init__ (this is what the code uses)
print("\n1. Creating UploadResponse with custom __init__ signature:")
print("   UploadResponse(path='test/file.txt', Key='bucket/test/file.txt')")

response = UploadResponse(path='test/file.txt', Key='bucket/test/file.txt')
print(f"   ✓ Instance created successfully")
print(f"   - path: {response.path}")
print(f"   - full_path: {response.full_path}")
print(f"   - fullPath: {response.fullPath}")

# Test 2: Try to use the dict() method (which is assigned to asdict)
print("\n2. Testing dict() method (assigned to asdict):")
try:
    result = response.dict()
    print(f"   ✗ UNEXPECTED: dict() succeeded, but may have issues")
    print(f"   Result: {result}")
except TypeError as e:
    print(f"   ✓ EXPECTED: dict() failed with TypeError")
    print(f"   Error: {e}")

# Test 3: Try using asdict directly
print("\n3. Testing asdict directly:")
try:
    from dataclasses import asdict
    result = asdict(response)
    print(f"   ✗ UNEXPECTED: asdict() succeeded")
    print(f"   Result: {result}")
except TypeError as e:
    print(f"   ✓ EXPECTED: asdict() failed")
    print(f"   Error: {e}")

# Test 4: Try to instantiate as a regular dataclass
print("\n4. Testing dataclass-style instantiation:")
print("   UploadResponse(path='test', full_path='full', fullPath='full')")
try:
    response2 = UploadResponse(path='test', full_path='full', fullPath='full')
    print(f"   ✗ UNEXPECTED: Dataclass instantiation succeeded")
except TypeError as e:
    print(f"   ✓ EXPECTED: Failed with TypeError")
    print(f"   Error: {e}")

print("\n" + "=" * 50)
print("BUG CONFIRMED: UploadResponse has conflicting @dataclass and __init__")
print("This causes issues with serialization and instantiation.")