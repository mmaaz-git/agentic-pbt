#!/usr/bin/env python3
"""Minimal reproduction of title validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.lightsail as lightsail

# Test empty string title - should raise ValueError but doesn't
print("Testing empty string title...")
try:
    instance = lightsail.Instance(
        title="",  # Empty string should be invalid
        BlueprintId="amazon_linux_2",
        BundleId="nano_2_0",
        InstanceName="test"
    )
    print(f"BUG: Empty string accepted as title! Title is: '{instance.title}'")
    print(f"Title validation did not raise ValueError as expected")
    
    # Can we even serialize it?
    result = instance.to_dict()
    print(f"Serialized successfully with empty title")
    print(f"Resource key in template would be: ''")
    
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")

print("\n" + "="*50 + "\n")

# Test with spaces in title - should also be invalid
print("Testing title with space...")
try:
    instance2 = lightsail.Instance(
        title="My Instance",  # Has space, should be invalid
        BlueprintId="amazon_linux_2",
        BundleId="nano_2_0",
        InstanceName="test"
    )
    print(f"BUG: Title with space accepted! Title is: '{instance2.title}'")
    
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")

print("\n" + "="*50 + "\n")

# Test valid title for comparison
print("Testing valid alphanumeric title...")
try:
    instance3 = lightsail.Instance(
        title="MyInstance123",  # Valid alphanumeric
        BlueprintId="amazon_linux_2",
        BundleId="nano_2_0",
        InstanceName="test"
    )
    print(f"Valid title accepted: '{instance3.title}'")
    
except ValueError as e:
    print(f"Unexpectedly raised ValueError: {e}")