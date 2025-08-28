#!/usr/bin/env python3
"""Test the impact of empty/None titles in CloudFormation template generation"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import Template
import troposphere.dax as dax
import json

# Create a template
template = Template()

# Add a cluster with empty title
cluster1 = dax.Cluster(
    "",  # Empty title
    IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole",
    NodeType="dax.r3.large",
    ReplicationFactor=1
)

# Add a cluster with None title
cluster2 = dax.Cluster(
    None,  # None title
    IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole2",
    NodeType="dax.r3.large",
    ReplicationFactor=1
)

# Try to add to template
print("Adding resources to template...")
template.add_resource(cluster1)
template.add_resource(cluster2)

print("\nTemplate resources:")
for name, resource in template.resources.items():
    print(f"  Resource name: '{name}', Title: {resource.title}")

print("\nGenerated CloudFormation JSON:")
try:
    json_output = template.to_json()
    parsed = json.loads(json_output)
    
    print("Resources section:")
    for key, value in parsed.get("Resources", {}).items():
        print(f"  '{key}': Type={value.get('Type')}")
    
    print("\nFull template (first 500 chars):")
    print(json_output[:500])
    
except Exception as e:
    print(f"Error generating template: {e}")
    import traceback
    traceback.print_exc()