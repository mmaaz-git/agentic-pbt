#!/usr/bin/env python3
"""Direct property tests for troposphere.opsworkscm"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.opsworkscm as opsworkscm
from troposphere import Tags

print("Testing troposphere.opsworkscm properties...")

# Test 1: EngineAttribute round-trip
print("\n1. Testing EngineAttribute round-trip...")
ea = opsworkscm.EngineAttribute(Name="TestName", Value="TestValue")
ea_dict = ea.to_dict()
print(f"   Original to_dict: {ea_dict}")
ea_restored = opsworkscm.EngineAttribute.from_dict(None, ea_dict)
ea_restored_dict = ea_restored.to_dict()
print(f"   Restored to_dict: {ea_restored_dict}")
print(f"   Are they equal? {ea == ea_restored}")
print(f"   Dicts equal? {ea_dict == ea_restored_dict}")

# Test 2: Server with minimal required fields
print("\n2. Testing Server with required fields...")
server = opsworkscm.Server(
    "MyServer",
    InstanceProfileArn="arn:aws:iam::123456789012:instance-profile/MyProfile",
    InstanceType="m5.large",
    ServiceRoleArn="arn:aws:iam::123456789012:role/MyRole"
)
server_dict = server.to_dict()
print(f"   Server dict keys: {server_dict.keys()}")
print(f"   Properties: {server_dict.get('Properties', {}).keys()}")

# Test 3: Server round-trip
print("\n3. Testing Server round-trip...")
props = server_dict.get('Properties', {})
server_restored = opsworkscm.Server.from_dict("MyServer", props)
server_restored_dict = server_restored.to_dict()
print(f"   Original == Restored? {server == server_restored}")
print(f"   Dicts equal? {server_dict == server_restored_dict}")

# Test 4: Hash consistency
print("\n4. Testing hash consistency...")
server2 = opsworkscm.Server(
    "MyServer",
    InstanceProfileArn="arn:aws:iam::123456789012:instance-profile/MyProfile",
    InstanceType="m5.large",
    ServiceRoleArn="arn:aws:iam::123456789012:role/MyRole"
)
print(f"   server1 == server2? {server == server2}")
print(f"   hash(server1) = {hash(server)}")
print(f"   hash(server2) = {hash(server2)}")
print(f"   Hashes equal? {hash(server) == hash(server2)}")

# Test 5: Invalid title
print("\n5. Testing invalid title...")
try:
    bad_server = opsworkscm.Server(
        "My-Server!",  # Contains non-alphanumeric characters
        InstanceProfileArn="arn",
        InstanceType="type",
        ServiceRoleArn="arn"
    )
    print("   ERROR: Invalid title was accepted!")
except ValueError as e:
    print(f"   Good: Invalid title rejected with: {e}")

# Test 6: Missing required field
print("\n6. Testing missing required field...")
try:
    incomplete = opsworkscm.Server(
        "TestServer",
        InstanceType="m5.large",
        ServiceRoleArn="arn"
        # Missing InstanceProfileArn
    )
    incomplete.to_dict()  # Should trigger validation
    print("   ERROR: Missing required field was not caught!")
except ValueError as e:
    print(f"   Good: Missing field caught with: {e}")

print("\nAll manual tests completed!")