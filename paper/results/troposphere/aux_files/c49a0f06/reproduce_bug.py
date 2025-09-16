#!/usr/bin/env python3
"""Minimal reproduction of the empty title validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.dax as dax

# Test 1: Empty string as title
print("Test 1: Creating Cluster with empty title...")
try:
    cluster = dax.Cluster(
        "",  # Empty title
        IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole",
        NodeType="dax.r3.large",
        ReplicationFactor=1
    )
    print(f"✗ BUG: Empty title accepted! cluster.title = '{cluster.title}'")
    
    # Can it be added to a template and converted to dict?
    dict_repr = cluster.to_dict()
    print(f"  to_dict() succeeded with empty title")
    print(f"  Resource type: {dict_repr.get('Type')}")
    
except ValueError as e:
    print(f"✓ Empty title rejected with error: {e}")

print()

# Test 2: None as title  
print("Test 2: Creating Cluster with None title...")
try:
    cluster2 = dax.Cluster(
        None,  # None title
        IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole",
        NodeType="dax.r3.large",
        ReplicationFactor=1
    )
    print(f"✗ BUG: None title accepted! cluster.title = {cluster2.title}")
    
    dict_repr2 = cluster2.to_dict()
    print(f"  to_dict() succeeded with None title")
    
except ValueError as e:
    print(f"✓ None title rejected with error: {e}")

print()

# Test 3: Non-alphanumeric title (should fail)
print("Test 3: Creating Cluster with non-alphanumeric title 'test-cluster'...")
try:
    cluster3 = dax.Cluster(
        "test-cluster",  # Has hyphen
        IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole",
        NodeType="dax.r3.large",
        ReplicationFactor=1
    )
    print(f"✗ Non-alphanumeric title accepted! cluster.title = '{cluster3.title}'")
except ValueError as e:
    print(f"✓ Non-alphanumeric title rejected with error: {e}")

print()

# Test 4: Valid alphanumeric title (should succeed)
print("Test 4: Creating Cluster with valid title 'TestCluster123'...")
try:
    cluster4 = dax.Cluster(
        "TestCluster123",
        IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole",
        NodeType="dax.r3.large",
        ReplicationFactor=1
    )
    print(f"✓ Valid title accepted! cluster.title = '{cluster4.title}'")
except ValueError as e:
    print(f"✗ Valid title rejected with error: {e}")