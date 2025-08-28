#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.inspectorv2 import *

# Test port range invariant
print("Testing PortRangeFilter invariants:")
try:
    # Valid range
    prf1 = PortRangeFilter(BeginInclusive=80, EndInclusive=443)
    print(f"Valid range [80, 443]: {prf1.properties}")
except Exception as e:
    print(f"Error: {e}")

try:
    # Invalid range (begin > end)
    prf2 = PortRangeFilter(BeginInclusive=443, EndInclusive=80)
    print(f"Invalid range [443, 80]: {prf2.properties}")
except Exception as e:
    print(f"Error: {e}")

# Test date filter invariant
print("\nTesting DateFilter invariants:")
try:
    # Valid range
    df1 = DateFilter(StartInclusive=100, EndInclusive=200)
    print(f"Valid range [100, 200]: {df1.properties}")
except Exception as e:
    print(f"Error: {e}")

try:
    # Invalid range (start > end)
    df2 = DateFilter(StartInclusive=200, EndInclusive=100)
    print(f"Invalid range [200, 100]: {df2.properties}")
except Exception as e:
    print(f"Error: {e}")

# Test number filter invariant
print("\nTesting NumberFilter invariants:")
try:
    # Valid range
    nf1 = NumberFilter(LowerInclusive=1.5, UpperInclusive=10.5)
    print(f"Valid range [1.5, 10.5]: {nf1.properties}")
except Exception as e:
    print(f"Error: {e}")

try:
    # Invalid range (lower > upper)
    nf2 = NumberFilter(LowerInclusive=10.5, UpperInclusive=1.5)
    print(f"Invalid range [10.5, 1.5]: {nf2.properties}")
except Exception as e:
    print(f"Error: {e}")

# Test edge cases
print("\nTesting edge cases:")

# Equal values in ranges
try:
    prf3 = PortRangeFilter(BeginInclusive=80, EndInclusive=80)
    print(f"Equal port range [80, 80]: {prf3.properties}")
except Exception as e:
    print(f"Error: {e}")

try:
    df3 = DateFilter(StartInclusive=100, EndInclusive=100)
    print(f"Equal date range [100, 100]: {df3.properties}")
except Exception as e:
    print(f"Error: {e}")

try:
    nf3 = NumberFilter(LowerInclusive=5.0, UpperInclusive=5.0)
    print(f"Equal number range [5.0, 5.0]: {nf3.properties}")
except Exception as e:
    print(f"Error: {e}")

# Negative values
try:
    prf4 = PortRangeFilter(BeginInclusive=-100, EndInclusive=100)
    print(f"Negative port begin [-100, 100]: {prf4.properties}")
except Exception as e:
    print(f"Error: {e}")

try:
    df4 = DateFilter(StartInclusive=-100, EndInclusive=100)
    print(f"Negative date start [-100, 100]: {df4.properties}")
except Exception as e:
    print(f"Error: {e}")

try:
    nf4 = NumberFilter(LowerInclusive=-10.5, UpperInclusive=10.5)
    print(f"Negative number lower [-10.5, 10.5]: {nf4.properties}")
except Exception as e:
    print(f"Error: {e}")

# Very large values
try:
    prf5 = PortRangeFilter(BeginInclusive=0, EndInclusive=999999)
    print(f"Large port range [0, 999999]: {prf5.properties}")
except Exception as e:
    print(f"Error: {e}")