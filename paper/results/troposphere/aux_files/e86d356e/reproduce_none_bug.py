#!/usr/bin/env python3
"""Minimal reproduction of the None handling bug in troposphere.cassandra."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cassandra as cassandra

# Test 1: ClusteringKeyColumns with None
print("Test 1: Creating Table with ClusteringKeyColumns=None")
try:
    table = cassandra.Table(
        title="TestTable",
        KeyspaceName="test_keyspace",
        PartitionKeyColumns=[
            cassandra.Column(ColumnName="id", ColumnType="uuid")
        ],
        ClusteringKeyColumns=None  # This is marked as optional in props
    )
    print("  SUCCESS: Table created with ClusteringKeyColumns=None")
    result = table.to_dict()
    print(f"  Properties: {result.get('Properties', {}).keys()}")
except TypeError as e:
    print(f"  FAILED: {e}")


# Test 2: RegularColumns with None  
print("\nTest 2: Creating Table with RegularColumns=None")
try:
    table = cassandra.Table(
        title="TestTable2",
        KeyspaceName="test_keyspace",
        PartitionKeyColumns=[
            cassandra.Column(ColumnName="id", ColumnType="uuid")
        ],
        RegularColumns=None  # Also optional
    )
    print("  SUCCESS: Table created with RegularColumns=None")
    result = table.to_dict()
    print(f"  Properties: {result.get('Properties', {}).keys()}")
except TypeError as e:
    print(f"  FAILED: {e}")


# Test 3: Simply omitting the optional properties
print("\nTest 3: Creating Table without specifying optional properties")
try:
    table = cassandra.Table(
        title="TestTable3",
        KeyspaceName="test_keyspace",
        PartitionKeyColumns=[
            cassandra.Column(ColumnName="id", ColumnType="uuid")
        ]
        # Not specifying ClusteringKeyColumns or RegularColumns at all
    )
    print("  SUCCESS: Table created without optional properties")
    result = table.to_dict()
    print(f"  Properties: {result.get('Properties', {}).keys()}")
except TypeError as e:
    print(f"  FAILED: {e}")


# Test 4: Using empty list instead of None
print("\nTest 4: Creating Table with empty lists for optional properties")
try:
    table = cassandra.Table(
        title="TestTable4",
        KeyspaceName="test_keyspace",
        PartitionKeyColumns=[
            cassandra.Column(ColumnName="id", ColumnType="uuid")
        ],
        ClusteringKeyColumns=[],  # Empty list instead of None
        RegularColumns=[]  # Empty list instead of None
    )
    print("  SUCCESS: Table created with empty lists")
    result = table.to_dict()
    print(f"  Properties: {result.get('Properties', {}).keys()}")
    print(f"  ClusteringKeyColumns: {result['Properties'].get('ClusteringKeyColumns')}")
    print(f"  RegularColumns: {result['Properties'].get('RegularColumns')}")
except TypeError as e:
    print(f"  FAILED: {e}")


# Test 5: Other optional properties with None
print("\nTest 5: Testing other optional properties with None")
try:
    keyspace = cassandra.Keyspace(
        title="TestKeyspace",
        KeyspaceName="test",
        ReplicationSpecification=None  # Optional property
    )
    print("  SUCCESS: Keyspace created with ReplicationSpecification=None")
except Exception as e:
    print(f"  FAILED: {e}")


# Analysis
print("\n" + "="*60)
print("ANALYSIS:")
print("="*60)
print("The troposphere library has inconsistent handling of None values")
print("for optional list properties:")
print("")
print("1. When optional list properties are omitted, it works fine")
print("2. When optional list properties are set to empty lists, it works")  
print("3. When optional list properties are explicitly set to None, it fails")
print("")
print("This is problematic because:")
print("- The properties are marked as optional (False) in the props definition")
print("- Users might reasonably expect None to be accepted for optional properties")
print("- The error message is confusing - it says NoneType isn't accepted")
print("  but doesn't clarify that omitting the property entirely would work")
print("")
print("This affects properties expecting lists like ClusteringKeyColumns,")
print("RegularColumns, ReplicaSpecifications, etc.")