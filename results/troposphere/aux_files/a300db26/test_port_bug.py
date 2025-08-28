#!/usr/bin/env python3
"""Test if Port properties incorrectly accept float values."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import mediaconnect

# Test if Port (which should be integer) accepts float values
print("Testing BridgeNetworkOutput with float Port value...")

output = mediaconnect.BridgeNetworkOutput(
    IpAddress="192.168.1.1",
    NetworkName="test",
    Port=8080.5,  # This should be rejected but isn't
    Protocol="tcp",
    Ttl=255
)

print(f"Port value stored: {output.properties['Port']}")
print(f"Port type: {type(output.properties['Port'])}")

# Test serialization
dict_repr = output.to_dict()
print(f"Serialized Port: {dict_repr['Port']}")
print(f"Serialized Port type: {type(dict_repr['Port'])}")

# This is problematic because AWS CloudFormation expects integer ports
print("\nThis is a bug because:")
print("1. Port numbers must be integers in networking")
print("2. AWS CloudFormation expects integer values for Port")
print("3. A float port like 8080.5 is invalid and should be rejected")