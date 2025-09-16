import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.memorydb as memorydb
from troposphere.validators import boolean, integer
import inspect

# Explore the module
print("=== Classes in troposphere.memorydb ===")
for name in dir(memorydb):
    obj = getattr(memorydb, name)
    if inspect.isclass(obj) and hasattr(obj, 'props'):
        print(f"\n{name}:")
        print(f"  Required props: {[k for k, v in obj.props.items() if v[1]]}")
        print(f"  Optional props: {[k for k, v in obj.props.items() if not v[1]]}")

# Look at validators
print("\n=== Validator functions ===")
print("boolean validator source:")
try:
    print(inspect.getsource(boolean))
except:
    print("Could not get source")

print("\ninteger validator source:")
try:
    print(inspect.getsource(integer))
except:
    print("Could not get source")

# Test basic functionality
print("\n=== Testing basic functionality ===")
try:
    acl = memorydb.ACL("TestACL", ACLName="test-acl")
    print(f"Created ACL: {acl.to_dict()}")
except Exception as e:
    print(f"Failed to create ACL: {e}")

try:
    # Missing required property
    cluster = memorydb.Cluster("TestCluster", ClusterName="test")
    print("Created cluster without all required props - this should have failed!")
except Exception as e:
    print(f"Expected failure for missing required props: {e}")