"""Minimal reproduction of empty title validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.pcs as pcs

# Bug: Empty string is accepted as a valid title
print("Testing Cluster creation with empty title...")
try:
    cluster = pcs.Cluster(
        "",  # Empty title should be rejected
        Networking=pcs.Networking(SubnetIds=["subnet-123"]),
        Scheduler=pcs.Scheduler(Type="SLURM", Version="23.11"),
        Size="SMALL"
    )
    print(f"BUG - Empty title was accepted. Cluster created: {cluster.title}")
    # Try to trigger validation
    cluster.to_dict()
    print("BUG - Empty title passed full validation")
except ValueError as e:
    print(f"Expected ValueError: {e}")

print("\nTesting with None title...")
try:
    cluster = pcs.Cluster(
        None,  # None title
        Networking=pcs.Networking(SubnetIds=["subnet-123"]),
        Scheduler=pcs.Scheduler(Type="SLURM", Version="23.11"),
        Size="SMALL"
    )
    print(f"Title is: {cluster.title}")
    cluster.to_dict()
    print("None title was accepted")
except ValueError as e:
    print(f"ValueError: {e}")

print("\nTesting with special characters title...")
try:
    cluster = pcs.Cluster(
        "test-cluster",  # Has hyphen, should be rejected
        Networking=pcs.Networking(SubnetIds=["subnet-123"]),
        Scheduler=pcs.Scheduler(Type="SLURM", Version="23.11"),
        Size="SMALL"
    )
    print(f"Title with hyphen was accepted: {cluster.title}")
except ValueError as e:
    print(f"Expected ValueError for hyphen: {e}")