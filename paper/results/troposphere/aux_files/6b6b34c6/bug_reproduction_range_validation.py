#!/usr/bin/env python3
"""Bug: Range filters don't validate that begin <= end"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.inspectorv2 import PortRangeFilter, DateFilter, NumberFilter

print("BUG 2: Missing Range Validation")
print("=" * 50)

print("\n1. PortRangeFilter accepts invalid ranges:")
# Valid range
valid_prf = PortRangeFilter(BeginInclusive=80, EndInclusive=443)
print(f"   Valid:   PortRangeFilter(BeginInclusive=80, EndInclusive=443)")
print(f"            Properties: {valid_prf.properties}")

# Invalid range (begin > end)
invalid_prf = PortRangeFilter(BeginInclusive=443, EndInclusive=80)
print(f"   Invalid: PortRangeFilter(BeginInclusive=443, EndInclusive=80)")
print(f"            Properties: {invalid_prf.properties}")
print(f"   Bug: Accepts invalid range where 443 > 80")

print("\n2. DateFilter accepts invalid ranges:")
# Valid range
valid_df = DateFilter(StartInclusive=100, EndInclusive=200)
print(f"   Valid:   DateFilter(StartInclusive=100, EndInclusive=200)")
print(f"            Properties: {valid_df.properties}")

# Invalid range (start > end)
invalid_df = DateFilter(StartInclusive=200, EndInclusive=100)
print(f"   Invalid: DateFilter(StartInclusive=200, EndInclusive=100)")
print(f"            Properties: {invalid_df.properties}")
print(f"   Bug: Accepts invalid range where 200 > 100")

print("\n3. NumberFilter accepts invalid ranges:")
# Valid range
valid_nf = NumberFilter(LowerInclusive=1.5, UpperInclusive=10.5)
print(f"   Valid:   NumberFilter(LowerInclusive=1.5, UpperInclusive=10.5)")
print(f"            Properties: {valid_nf.properties}")

# Invalid range (lower > upper)
invalid_nf = NumberFilter(LowerInclusive=10.5, UpperInclusive=1.5)
print(f"   Invalid: NumberFilter(LowerInclusive=10.5, UpperInclusive=1.5)")
print(f"            Properties: {invalid_nf.properties}")
print(f"   Bug: Accepts invalid range where 10.5 > 1.5")

print("\n4. Edge cases also problematic:")
# Negative port numbers (should be 0-65535)
negative_prf = PortRangeFilter(BeginInclusive=-100, EndInclusive=100)
print(f"   PortRangeFilter(BeginInclusive=-100, EndInclusive=100)")
print(f"   Properties: {negative_prf.properties}")
print(f"   Bug: Accepts negative port number -100")

# Port number > 65535
large_prf = PortRangeFilter(BeginInclusive=0, EndInclusive=999999)
print(f"   PortRangeFilter(BeginInclusive=0, EndInclusive=999999)")
print(f"   Properties: {large_prf.properties}")
print(f"   Bug: Accepts port number 999999 > 65535")

print("\n\nWhy this is a bug:")
print("- Invalid ranges are semantically incorrect")
print("- CloudFormation will likely reject these during deployment")
print("- Fails early validation principle - errors should be caught as soon as possible")
print("- Port numbers have well-defined valid range (0-65535)")
print("- Date/time ranges should follow natural ordering")