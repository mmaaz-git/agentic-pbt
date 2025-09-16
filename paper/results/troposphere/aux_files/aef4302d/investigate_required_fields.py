#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.kendra as kendra

print("=== Testing required field validation ===\n")

# Test 1: Missing required field
print("Test 1: Creating CapacityUnitsConfiguration with only QueryCapacityUnits:")
try:
    config1 = kendra.CapacityUnitsConfiguration(QueryCapacityUnits=10)
    print(f"  ✓ Created successfully: {config1.to_dict()}")
    print(f"  This is a BUG - StorageCapacityUnits is marked as required but not enforced!")
except Exception as e:
    print(f"  ✗ Failed as expected: {e}")

print("\nTest 2: Creating CapacityUnitsConfiguration with only StorageCapacityUnits:")
try:
    config2 = kendra.CapacityUnitsConfiguration(StorageCapacityUnits=20)
    print(f"  ✓ Created successfully: {config2.to_dict()}")
    print(f"  This is a BUG - QueryCapacityUnits is marked as required but not enforced!")
except Exception as e:
    print(f"  ✗ Failed as expected: {e}")

print("\nTest 3: Creating CapacityUnitsConfiguration with no fields:")
try:
    config3 = kendra.CapacityUnitsConfiguration()
    print(f"  ✓ Created successfully: {config3.to_dict()}")
    print(f"  This is a BUG - Both fields are required but can be omitted!")
except Exception as e:
    print(f"  ✗ Failed as expected: {e}")

print("\n=== Checking the props definition ===")
print(f"CapacityUnitsConfiguration.props: {kendra.CapacityUnitsConfiguration.props}")

print("\n=== Testing other required fields ===")

# Test ConnectionConfiguration which has many required fields
print("\nTest 4: Creating ConnectionConfiguration with missing required fields:")
try:
    conn = kendra.ConnectionConfiguration(DatabaseHost="localhost")
    print(f"  ✓ Created successfully: {conn.to_dict()}")
    print(f"  This is a BUG - Missing required fields: DatabaseName, DatabasePort, SecretArn, TableName")
except Exception as e:
    print(f"  ✗ Failed as expected: {e}")

# Test AclConfiguration with required field
print("\nTest 5: Creating AclConfiguration without required AllowedGroupsColumnName:")
try:
    acl = kendra.AclConfiguration()
    print(f"  ✓ Created successfully: {acl.to_dict()}")
    print(f"  This is a BUG - AllowedGroupsColumnName is required but can be omitted!")
except Exception as e:
    print(f"  ✗ Failed as expected: {e}")

print("\n=== Summary ===")
print("The 'required' flag in the props definition is NOT enforced during instantiation!")
print("Classes can be created with missing required fields, which violates the API contract.")