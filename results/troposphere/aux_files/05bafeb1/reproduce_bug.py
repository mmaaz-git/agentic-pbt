#!/usr/bin/env python3
"""Minimal reproduction of the bug in troposphere classes"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.groundstation import IntegerRange, Bandwidth

# Bug 1: IntegerRange.to_dict() returns empty dict even when properties are set
print("Bug 1: IntegerRange.to_dict() issue")
int_range = IntegerRange()
int_range.properties = {"Minimum": 10, "Maximum": 20}
print(f"Properties set: {int_range.properties}")
result = int_range.to_dict()
print(f"to_dict() result: {result}")
print(f"Expected: {{'Minimum': 10, 'Maximum': 20}}")
print()

# Bug 2: Similar issue with Bandwidth
print("Bug 2: Bandwidth.to_dict() issue")
bandwidth = Bandwidth()
bandwidth.properties = {"Value": 100.0, "Units": "MHz"}
print(f"Properties set: {bandwidth.properties}")
result = bandwidth.to_dict()
print(f"to_dict() result: {result}")
print(f"Expected: {{'Value': 100.0, 'Units': 'MHz'}}")
print()

# Let's try the proper way to set properties
print("Trying proper initialization with keyword arguments:")
try:
    int_range2 = IntegerRange(Minimum=10, Maximum=20)
    print(f"Properties: {int_range2.properties}")
    result2 = int_range2.to_dict()
    print(f"to_dict() result: {result2}")
except Exception as e:
    print(f"Error: {e}")

print()

# Let's check how the class is supposed to be used
print("Checking the actual props definition:")
print(f"IntegerRange.props: {IntegerRange.props}")
print(f"Bandwidth.props: {Bandwidth.props}")