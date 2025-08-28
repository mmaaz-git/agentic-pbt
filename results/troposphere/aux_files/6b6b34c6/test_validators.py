#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer, double
from troposphere.inspectorv2 import *
import math

print("Testing integer validator:")
test_integer_values = [
    # Valid integers
    (42, "int"),
    ("42", "str"),
    (42.0, "float"),
    (True, "bool True"),
    (False, "bool False"),
    # Edge cases
    (0, "zero"),
    (-1, "negative"),
    (2**31 - 1, "max 32-bit"),
    (2**63 - 1, "max 64-bit"),
    # Invalid
    ("not_a_number", "string"),
    (None, "None"),
    ([], "empty list"),
    (float('inf'), "infinity"),
    (float('nan'), "nan"),
    ("42.5", "float string"),
]

for val, desc in test_integer_values:
    try:
        result = integer(val)
        print(f"  {desc:15} ({val}): Accepted -> {result}")
    except Exception as e:
        print(f"  {desc:15} ({val}): Rejected - {type(e).__name__}: {e}")

print("\nTesting double validator:")
test_double_values = [
    # Valid doubles
    (42.5, "float"),
    ("42.5", "str float"),
    (42, "int"),
    ("42", "str int"),
    (0.0, "zero float"),
    (-1.5, "negative float"),
    (1e10, "scientific"),
    (1e-10, "small scientific"),
    # Edge cases
    (float('inf'), "infinity"),
    (float('-inf'), "neg infinity"),
    (float('nan'), "nan"),
    # Invalid
    ("not_a_number", "string"),
    (None, "None"),
    ([], "empty list"),
]

for val, desc in test_double_values:
    try:
        result = double(val)
        print(f"  {desc:15} ({val}): Accepted -> {result}")
    except Exception as e:
        print(f"  {desc:15} ({val}): Rejected - {type(e).__name__}: {e}")

print("\nTesting validators in filter classes:")

# Test that validators are actually called
print("\n1. PortRangeFilter with integer validator:")
try:
    prf = PortRangeFilter(BeginInclusive="42", EndInclusive=100)
    print(f"  String '42' accepted: {prf.properties}")
except Exception as e:
    print(f"  String '42' rejected: {e}")

try:
    prf = PortRangeFilter(BeginInclusive=42.5, EndInclusive=100)
    print(f"  Float 42.5 accepted: {prf.properties}")
except Exception as e:
    print(f"  Float 42.5 rejected: {e}")

print("\n2. NumberFilter with double validator:")
try:
    nf = NumberFilter(LowerInclusive="42.5", UpperInclusive=100)
    print(f"  String '42.5' accepted: {nf.properties}")
except Exception as e:
    print(f"  String '42.5' rejected: {e}")

try:
    nf = NumberFilter(LowerInclusive=float('inf'), UpperInclusive=100)
    print(f"  Infinity accepted: {nf.properties}")
except Exception as e:
    print(f"  Infinity rejected: {e}")

try:
    nf = NumberFilter(LowerInclusive=float('nan'), UpperInclusive=100)
    print(f"  NaN accepted: {nf.properties}")
    # Check if NaN is preserved
    if math.isnan(nf.properties.get('LowerInclusive', 0)):
        print("    NaN was preserved in properties")
except Exception as e:
    print(f"  NaN rejected: {e}")

# Test type coercion
print("\n3. Type preservation after validation:")
prf = PortRangeFilter(BeginInclusive="42", EndInclusive="100")
print(f"  Input types: str('42'), str('100')")
print(f"  Output types: {type(prf.properties['BeginInclusive'])}({prf.properties['BeginInclusive']}), {type(prf.properties['EndInclusive'])}({prf.properties['EndInclusive']})")

nf = NumberFilter(LowerInclusive="42.5", UpperInclusive="100.5")
print(f"  Input types: str('42.5'), str('100.5')")
print(f"  Output types: {type(nf.properties['LowerInclusive'])}({nf.properties['LowerInclusive']}), {type(nf.properties['UpperInclusive'])}({nf.properties['UpperInclusive']})")