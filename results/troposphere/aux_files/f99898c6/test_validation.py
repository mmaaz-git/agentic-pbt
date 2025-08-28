import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.memorydb as memorydb

print("=== Testing required property validation ===")

# Test 1: Missing required property should fail on to_dict()
try:
    cluster = memorydb.Cluster("TestCluster", ClusterName="test")
    # This should succeed
    print("Created cluster without all required props")
    
    # But this should fail
    cluster.to_dict()
    print("ERROR: to_dict() succeeded when it should have failed!")
except ValueError as e:
    print(f"Expected failure on to_dict(): {e}")

# Test 2: All required properties provided
try:
    cluster = memorydb.Cluster("TestCluster", 
                               ClusterName="test",
                               ACLName="test-acl",
                               NodeType="db.t4g.small")
    result = cluster.to_dict()
    print(f"Successfully created cluster with all required props: {result}")
except Exception as e:
    print(f"Unexpected error: {e}")

# Test 3: Type validation
print("\n=== Testing type validation ===")
try:
    # Port should be an integer
    endpoint = memorydb.Endpoint(Port="not-an-integer")
    print(f"Created Endpoint with invalid port type")
    result = endpoint.to_dict()
    print(f"Result: {result}")
except Exception as e:
    print(f"Type validation error: {e}")

# Test 4: Boolean validation edge cases
print("\n=== Testing boolean validator edge cases ===")
from troposphere.validators import boolean

test_cases = [
    "TRUE",  # uppercase
    "FALSE", # uppercase
    "tRuE",  # mixed case
    "fAlSe", # mixed case
    " true", # with space
    "true ", # with space
    "yes",   # not a valid boolean string
    "",      # empty string
]

for test in test_cases:
    try:
        result = boolean(test)
        print(f"boolean('{test}') = {result}")
    except ValueError:
        print(f"boolean('{test}') raised ValueError")

# Test 5: Integer validator edge cases
print("\n=== Testing integer validator ===")
from troposphere.validators import integer

int_test_cases = [
    42,
    "42",
    "42.0",
    42.0,
    "  42  ",
    "-42",
    "0x2a",  # hex
    "",
    None,
    "not_a_number",
]

for test in int_test_cases:
    try:
        result = integer(test)
        print(f"integer({repr(test)}) = {repr(result)}")
    except (ValueError, TypeError) as e:
        print(f"integer({repr(test)}) raised {type(e).__name__}")