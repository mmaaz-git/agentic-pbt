#!/usr/bin/env python3
"""Verify the bug: properties vs resource mismatch"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.groundstation import IntegerRange

# Create an IntegerRange properly
int_range1 = IntegerRange(Minimum=10, Maximum=20)
print("Properly initialized IntegerRange:")
print(f"  properties: {int_range1.properties}")
print(f"  resource: {int_range1.resource}")
print(f"  Are they the same object? {int_range1.properties is int_range1.resource}")
print(f"  to_dict(): {int_range1.to_dict()}")
print()

# Create an IntegerRange and modify properties directly
int_range2 = IntegerRange()
print("IntegerRange with empty init:")
print(f"  properties: {int_range2.properties}")
print(f"  resource: {int_range2.resource}")
print(f"  Are they the same object? {int_range2.properties is int_range2.resource}")
print()

# Now directly assign to properties
int_range2.properties = {"Minimum": 30, "Maximum": 40}
print("After directly setting properties:")
print(f"  properties: {int_range2.properties}")
print(f"  resource: {int_range2.resource}")
print(f"  Are they the same object? {int_range2.properties is int_range2.resource}")
print(f"  to_dict(): {int_range2.to_dict()}")
print()

# What if we try to update resource instead?
int_range3 = IntegerRange()
int_range3.resource["Minimum"] = 50
int_range3.resource["Maximum"] = 60
print("IntegerRange with resource updated:")
print(f"  properties: {int_range3.properties}")
print(f"  resource: {int_range3.resource}")
print(f"  to_dict(): {int_range3.to_dict()}")