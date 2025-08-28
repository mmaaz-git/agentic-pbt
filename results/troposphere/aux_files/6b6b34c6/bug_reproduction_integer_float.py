#!/usr/bin/env python3
"""Bug: Integer validator accepts float values"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer
from troposphere.inspectorv2 import PortRangeFilter

print("BUG 3: Integer Validator Accepts Floats")
print("=" * 50)

print("\n1. Integer validator with float inputs:")
test_values = [
    42.0,   # Integer as float
    42.5,   # Non-integer float
    42.9,   # Non-integer float
    -10.3,  # Negative non-integer
]

for val in test_values:
    try:
        result = integer(val)
        print(f"   integer({val}) returns: {result!r} (type: {type(result).__name__})")
        if val != int(val):
            print(f"   Bug: Accepted non-integer float {val}")
    except Exception as e:
        print(f"   integer({val}) raised: {type(e).__name__}: {e}")

print("\n2. Impact on PortRangeFilter:")
# Port ranges should be integers, not floats
prf = PortRangeFilter(BeginInclusive=80.5, EndInclusive=443.9)
print(f"   PortRangeFilter(BeginInclusive=80.5, EndInclusive=443.9)")
print(f"   Properties: {prf.properties}")
print(f"   Bug: Accepts non-integer port numbers 80.5 and 443.9")

print("\n3. Semantic issues:")
print("   - Port numbers must be integers (you can't bind to port 80.5)")
print("   - DateFilter timestamps should be integers (Unix timestamps)")
print("   - Accepting floats violates the semantic meaning of 'integer'")

print("\n\nWhy this is a bug:")
print("- The validator is named 'integer' but accepts non-integers")
print("- Port numbers, timestamps, and counts must be whole numbers")
print("- CloudFormation likely expects true integers for these fields")
print("- Violates principle of least surprise")
print("- Could lead to subtle bugs when float values are passed downstream")