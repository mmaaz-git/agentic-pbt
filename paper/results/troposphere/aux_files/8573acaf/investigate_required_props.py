"""Investigate how required properties work in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import cloudfront

# Test 1: Can we create DefaultCacheBehavior without required properties?
try:
    behavior = cloudfront.DefaultCacheBehavior()
    print("DefaultCacheBehavior created without any properties!")
    print("Properties:", behavior.properties)
except Exception as e:
    print(f"Failed to create DefaultCacheBehavior: {e}")

# Test 2: With only one required property
try:
    behavior = cloudfront.DefaultCacheBehavior(TargetOriginId="origin1")
    print("\nDefaultCacheBehavior created with only TargetOriginId!")
    print("Properties:", behavior.properties)
except Exception as e:
    print(f"Failed with only TargetOriginId: {e}")

# Test 3: Check if validation happens later
try:
    behavior = cloudfront.DefaultCacheBehavior()
    # Try to convert to dict (which might trigger validation)
    behavior_dict = behavior.to_dict()
    print("\nConverted to dict without required properties:")
    print(behavior_dict)
except Exception as e:
    print(f"Failed during to_dict: {e}")

# Test 4: Check the props definition
print("\nDefaultCacheBehavior required properties:")
for prop_name, (prop_type, is_required) in cloudfront.DefaultCacheBehavior.props.items():
    if is_required:
        print(f"  - {prop_name}: required={is_required}")

# Test 5: Try with explicit validation
from troposphere import Template

template = Template()
try:
    behavior = cloudfront.DefaultCacheBehavior()
    # Add to template which might trigger validation
    dist = cloudfront.Distribution(
        "TestDist",
        DistributionConfig=cloudfront.DistributionConfig(
            DefaultCacheBehavior=behavior,
            Enabled=True
        )
    )
    template.add_resource(dist)
    json_output = template.to_json()
    print("\nTemplate created successfully without required properties!")
except Exception as e:
    print(f"\nFailed during template creation: {e}")