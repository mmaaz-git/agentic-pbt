#!/usr/bin/env python3
"""Minimal reproduction of the validation bug in troposphere.redshift"""

import troposphere.redshift as redshift

# Create a Cluster object missing the required 'ClusterType' field
cluster = redshift.Cluster(
    'MyCluster',
    DBName='testdb',
    MasterUsername='admin',
    NodeType='dc2.large'
)

# The validate() method passes even though a required field is missing
cluster.validate()
print("✓ validate() passed (should have failed)")

# But to_dict() correctly fails
try:
    cluster.to_dict()
    print("✗ to_dict() passed (unexpected)")
except Exception as e:
    print(f"✓ to_dict() failed with: {e}")

print("\nThis inconsistency is a bug: validate() should check required fields")