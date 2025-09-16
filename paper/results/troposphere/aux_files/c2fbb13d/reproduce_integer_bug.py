#!/usr/bin/env python3
"""
Minimal reproduction of the integer validator bug in troposphere.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators
import troposphere.appmesh as appmesh

# Bug: integer validator accepts floats and silently truncates them
print("Testing integer validator with float 1.5:")
result = validators.integer(1.5)
print(f"  validators.integer(1.5) = {repr(result)}")
print(f"  int(result) = {int(result)}")

print("\nTesting integer validator with float 2.9:")
result = validators.integer(2.9)
print(f"  validators.integer(2.9) = {repr(result)}")
print(f"  int(result) = {int(result)}")

# This causes problems in actual use
print("\nReal-world impact - Duration with float Value:")
duration = appmesh.Duration(Unit='ms', Value=1.5)
print(f"  Duration(Unit='ms', Value=1.5).to_dict() = {duration.to_dict()}")

print("\nWeightedTarget with float Weight:")
wt = appmesh.WeightedTarget(VirtualNode='node', Weight=33.7)
print(f"  WeightedTarget(VirtualNode='node', Weight=33.7).to_dict() = {wt.to_dict()}")

print("\nPort mapping with float port:")
pm = appmesh.VirtualGatewayPortMapping(Port=8080.5, Protocol='http')
print(f"  VirtualGatewayPortMapping(Port=8080.5, Protocol='http').to_dict() = {pm.to_dict()}")