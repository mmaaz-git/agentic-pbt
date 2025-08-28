#!/usr/bin/env python3
"""Test for potential issues with empty titles."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cassandra as cassandra


# Test 1: Empty title in AWSObject
print("Test 1: Creating Keyspace with empty title")
try:
    keyspace = cassandra.Keyspace(
        title="",  # Empty title
        KeyspaceName="test"
    )
    result = keyspace.to_dict()
    print(f"  Result: {result}")
    print("  Issue: Empty title produces incomplete CloudFormation resource")
except Exception as e:
    print(f"  Error: {e}")


# Test 2: None title in AWSObject  
print("\nTest 2: Creating Keyspace with None title")
try:
    keyspace = cassandra.Keyspace(
        title=None,
        KeyspaceName="test"
    )
    result = keyspace.to_dict()
    print(f"  Result: {result}")
    print("  Issue: None title might cause problems when referencing")
except Exception as e:
    print(f"  Error: {e}")


# Test 3: Multiple resources with empty titles
print("\nTest 3: Multiple resources with empty titles")
try:
    ks1 = cassandra.Keyspace(title="", KeyspaceName="ks1")
    ks2 = cassandra.Keyspace(title="", KeyspaceName="ks2")
    
    # Try to use one as a dependency
    table = cassandra.Table(
        title="MyTable",
        KeyspaceName="test",
        PartitionKeyColumns=[
            cassandra.Column(ColumnName="id", ColumnType="uuid")
        ],
        DependsOn=ks1  # Reference to keyspace with empty title
    )
    result = table.to_dict()
    print(f"  DependsOn value: {result.get('DependsOn')}")
    print("  Issue: DependsOn with empty title resource produces empty string")
except Exception as e:
    print(f"  Error: {e}")


# Test 4: Using Ref with empty title
print("\nTest 4: Using Ref with empty title resource")
try:
    from troposphere import Ref
    
    keyspace = cassandra.Keyspace(title="", KeyspaceName="test")
    ref = keyspace.ref()  # or Ref(keyspace)
    print(f"  Ref value: {ref.to_dict()}")
    print("  Issue: Ref to empty-titled resource is problematic")
except Exception as e:
    print(f"  Error: {e}")


print("\n" + "=" * 60)
print("ANALYSIS:")
print("=" * 60)
print("Allowing empty/None titles creates several problems:")
print("")
print("1. CloudFormation resources need unique names in the template")
print("2. References (Ref, DependsOn) rely on the title")
print("3. Multiple resources with empty titles would conflict")
print("4. The title is used as the logical ID in CloudFormation")
print("")
print("The validation should probably enforce non-empty titles")
print("for AWSObject instances (resources) while allowing")
print("None/empty for AWSProperty instances (nested properties).")