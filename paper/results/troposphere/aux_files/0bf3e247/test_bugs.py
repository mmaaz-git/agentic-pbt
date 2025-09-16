#!/usr/bin/env python3
"""Standalone test to find bugs in troposphere.dms"""

import sys

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import network_port

# Test the network_port validator with edge cases
print("Testing network_port validator...")

# Test case 1: port -1 (should be accepted according to code)
try:
    result = network_port(-1)
    print(f"✓ network_port(-1) = {result} (accepted)")
except ValueError as e:
    print(f"✗ network_port(-1) raised ValueError: {e}")

# Test case 2: port 0 (should be accepted)
try:
    result = network_port(0)
    print(f"✓ network_port(0) = {result} (accepted)")
except ValueError as e:
    print(f"✗ network_port(0) raised ValueError: {e}")

# Test case 3: port -2 (should be rejected)
try:
    result = network_port(-2)
    print(f"✗ network_port(-2) = {result} (should have been rejected!)")
except ValueError as e:
    print(f"✓ network_port(-2) raised ValueError: {e}")
    # Check the error message
    error_msg = str(e)
    if "must been between 0 and 65535" in error_msg:
        print("  BUG FOUND: Error message says 'between 0 and 65535' but code accepts -1!")
        print(f"  Actual check in code: int(i) < -1 or int(i) > 65535")
        print(f"  This is a contract violation - the error message doesn't match the implementation")

print("\n" + "="*60 + "\n")

# Let's verify this more thoroughly
print("Comprehensive test of boundary values:")
test_values = [-3, -2, -1, 0, 1, 65534, 65535, 65536, 65537]

for port in test_values:
    try:
        result = network_port(port)
        status = "ACCEPTED"
    except ValueError as e:
        status = f"REJECTED with: {e}"
    
    print(f"  network_port({port:6d}) -> {status}")

print("\n" + "="*60 + "\n")
print("ANALYSIS:")
print("The network_port validator has a contract violation bug:")
print("1. The error message claims ports must be 'between 0 and 65535'")
print("2. The actual implementation accepts -1 as valid")
print("3. This inconsistency could confuse users and lead to unexpected behavior")
print("\nThe code at line 130 checks: int(i) < -1 or int(i) > 65535")
print("But the error at line 131 says: 'must been between 0 and 65535'")
print("\nAdditionally, there's a typo in the error message: 'must been' should be 'must be'")