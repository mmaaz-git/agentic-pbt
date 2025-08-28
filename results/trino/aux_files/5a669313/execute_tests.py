#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

import trino.constants as constants

print("Testing trino.constants properties...")
print("="*60)

# Test 1: Client capabilities concatenation
print("\n1. Testing CLIENT_CAPABILITIES concatenation...")
expected = ','.join([
    constants.CLIENT_CAPABILITY_PARAMETRIC_DATETIME,
    constants.CLIENT_CAPABILITY_SESSION_AUTHORIZATION
])
if constants.CLIENT_CAPABILITIES == expected:
    print("  ✓ PASSED: CLIENT_CAPABILITIES correctly concatenated")
else:
    print(f"  ✗ FAILED: Expected '{expected}', got '{constants.CLIENT_CAPABILITIES}'")

# Test 2: Header name pattern
print("\n2. Testing HEADER_* constants pattern...")
header_constants = [
    name for name in dir(constants) 
    if name.startswith('HEADER_') and not name.startswith('_')
]
all_valid = True
for header_name in header_constants:
    header_value = getattr(constants, header_name)
    if not isinstance(header_value, str) or not header_value.startswith('X-Trino-'):
        print(f"  ✗ FAILED: {header_name} = '{header_value}' doesn't follow X-Trino-* pattern")
        all_valid = False
if all_valid:
    print(f"  ✓ PASSED: All {len(header_constants)} header constants follow X-Trino-* pattern")

# Test 3: Scale types subset of precision types
print("\n3. Testing SCALE_TYPES subset of PRECISION_TYPES...")
scale_in_precision = all(st in constants.PRECISION_TYPES for st in constants.SCALE_TYPES)
if scale_in_precision:
    print("  ✓ PASSED: SCALE_TYPES is subset of PRECISION_TYPES")
else:
    print(f"  ✗ FAILED: SCALE_TYPES {constants.SCALE_TYPES} not subset of PRECISION_TYPES")

# Test 4: Protocol values
print("\n4. Testing protocol string values...")
if constants.HTTP == "http" and constants.HTTPS == "https":
    print("  ✓ PASSED: HTTP and HTTPS have correct lowercase values")
else:
    print(f"  ✗ FAILED: HTTP='{constants.HTTP}', HTTPS='{constants.HTTPS}'")

# Test 5: Default ports
print("\n5. Testing default port values...")
if constants.DEFAULT_PORT == 8080 and constants.DEFAULT_TLS_PORT == 443:
    print("  ✓ PASSED: Default ports have standard values")
else:
    print(f"  ✗ FAILED: DEFAULT_PORT={constants.DEFAULT_PORT}, DEFAULT_TLS_PORT={constants.DEFAULT_TLS_PORT}")

# Test 6: Constants mutability check
print("\n6. Testing list mutability...")
original_length = len(constants.LENGTH_TYPES)
try:
    constants.LENGTH_TYPES.append("test_mutation")
    if len(constants.LENGTH_TYPES) > original_length:
        print("  ⚠ WARNING: LENGTH_TYPES is mutable (list can be modified)")
        constants.LENGTH_TYPES.pop()  # Clean up
    else:
        print("  ✓ PASSED: Lists appear immutable")
except (AttributeError, TypeError):
    print("  ✓ PASSED: Lists are immutable")

print("\n" + "="*60)
print("Testing complete!")