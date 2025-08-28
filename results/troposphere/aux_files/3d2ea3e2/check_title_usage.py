#!/usr/bin/env python3
"""Check how titles are used in troposphere."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import cognito, Template

# Test 1: How does a template handle resources with empty titles?
print("Test 1: Template with empty-titled resource")
template = Template()
pool_empty = cognito.IdentityPool(
    title="",
    AllowUnauthenticatedIdentities=True
)
try:
    template.add_resource(pool_empty)
    print("  Added resource with empty title to template")
    print(f"  Template resources: {list(template.resources.keys())}")
except Exception as e:
    print(f"  Failed to add: {e}")

# Test 2: Template with None-titled resource
print("\nTest 2: Template with None-titled resource")
template2 = Template()
pool_none = cognito.IdentityPool(
    title=None,
    AllowUnauthenticatedIdentities=True
)
try:
    template2.add_resource(pool_none)
    print("  Added resource with None title to template")
    print(f"  Template resources: {list(template2.resources.keys())}")
except Exception as e:
    print(f"  Failed to add: {e}")

# Test 3: Normal usage with valid title
print("\nTest 3: Template with properly-titled resource")
template3 = Template()
pool_valid = cognito.IdentityPool(
    title="MyIdentityPool",
    AllowUnauthenticatedIdentities=True
)
try:
    template3.add_resource(pool_valid)
    print("  Added resource with valid title to template")
    print(f"  Template resources: {list(template3.resources.keys())}")
    # Try to generate JSON
    import json
    json_output = template3.to_json()
    parsed = json.loads(json_output)
    print(f"  Resource in JSON: {list(parsed.get('Resources', {}).keys())}")
except Exception as e:
    print(f"  Failed: {e}")

# Test 4: What if we have a resource with invalid characters?
print("\nTest 4: Resource with invalid title characters")
try:
    pool_invalid = cognito.IdentityPool(
        title="my-pool-name",  # has dashes
        AllowUnauthenticatedIdentities=True
    )
    print("  Created resource with dashes in title (unexpected!)")
except ValueError as e:
    print(f"  Correctly rejected: {e}")