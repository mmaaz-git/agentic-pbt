#!/usr/bin/env python3
"""Bug: Validators preserve input type instead of converting to expected type"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer, double
from troposphere.inspectorv2 import PortRangeFilter, NumberFilter

print("BUG 1: Type Preservation Issue")
print("=" * 50)

# Integer validator doesn't convert strings to integers
print("\n1. Integer validator with string input:")
result = integer("42")
print(f"   integer('42') returns: {result!r} (type: {type(result).__name__})")
print(f"   Expected: 42 (type: int)")
print(f"   Bug: Returns '42' (type: str)")

# Double validator doesn't convert strings to floats
print("\n2. Double validator with string input:")
result = double("42.5")
print(f"   double('42.5') returns: {result!r} (type: {type(result).__name__})")
print(f"   Expected: 42.5 (type: float)")
print(f"   Bug: Returns '42.5' (type: str)")

# This causes type inconsistency in filter properties
print("\n3. Impact on PortRangeFilter:")
prf = PortRangeFilter(BeginInclusive="80", EndInclusive=443)
print(f"   Input: BeginInclusive='80', EndInclusive=443")
print(f"   Properties: {prf.properties}")
print(f"   Types: BeginInclusive={type(prf.properties['BeginInclusive']).__name__}, EndInclusive={type(prf.properties['EndInclusive']).__name__}")
print(f"   Bug: Mixed types in properties (str and int)")

print("\n4. Impact on NumberFilter:")
nf = NumberFilter(LowerInclusive="1.5", UpperInclusive=10.5)
print(f"   Input: LowerInclusive='1.5', UpperInclusive=10.5")
print(f"   Properties: {nf.properties}")
print(f"   Types: LowerInclusive={type(nf.properties['LowerInclusive']).__name__}, UpperInclusive={type(nf.properties['UpperInclusive']).__name__}")
print(f"   Bug: Mixed types in properties (str and float)")

print("\n5. Comparison issues due to mixed types:")
prf2 = PortRangeFilter(BeginInclusive="100", EndInclusive=99)
print(f"   PortRangeFilter(BeginInclusive='100', EndInclusive=99)")
print(f"   Properties: {prf2.properties}")
print(f"   String '100' > int 99 in Python 3 causes TypeError in comparisons")
try:
    if prf2.properties['BeginInclusive'] > prf2.properties['EndInclusive']:
        print("   This comparison would fail with TypeError")
except TypeError as e:
    print(f"   TypeError: {e}")

print("\n\nWhy this is a bug:")
print("- Validators are meant to ensure correct data types")
print("- Mixed types in properties lead to comparison errors")
print("- CloudFormation expects consistent numeric types")
print("- Breaks principle of least surprise")