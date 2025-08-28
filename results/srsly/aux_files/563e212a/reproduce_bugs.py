#!/usr/bin/env python3
"""Minimal reproductions for bugs found in srsly.ujson"""

import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

import srsly.ujson as ujson

print("=== Bug 1: Float Precision Loss for Large Floats ===")
# Hypothesis found this value loses precision
test_float = 7.4350845423805815e+283
print(f"Original value: {test_float}")
encoded = ujson.dumps([test_float])
print(f"Encoded JSON: {encoded}")
decoded = ujson.loads(encoded)
print(f"Decoded value: {decoded[0]}")
print(f"Values equal? {decoded[0] == test_float}")
print(f"Precision lost: {abs(decoded[0] - test_float)}")

# Compare with standard json
json_encoded = json.dumps([test_float])
json_decoded = json.loads(json_encoded)
print(f"\nStandard json preserves value? {json_decoded[0] == test_float}")
print()

print("=== Bug 2: Integer Overflow for Large Negative Integers ===")
# Integer just below -(2^63)
test_int = -9223372036854775809  # -(2^63) - 1
print(f"Test integer: {test_int}")
try:
    encoded = ujson.dumps(test_int)
    print(f"Encoded: {encoded}")
except OverflowError as e:
    print(f"ERROR: {e}")

# Compare with standard json
try:
    json_encoded = json.dumps(test_int)
    print(f"Standard json handles it: {json_encoded}")
    json_decoded = json.loads(json_encoded)
    print(f"Standard json round-trip: {json_decoded == test_int}")
except Exception as e:
    print(f"Standard json also fails: {e}")
print()

print("=== Bug 3: Float Near Max Value Converts to Infinity ===")
# Float very close to max float value
test_float2 = 1.7976931348623155e+308  # Very close to sys.float_info.max
print(f"Test float: {test_float2}")
print(f"Is finite? {float(test_float2).__repr__() != 'inf'}")

encoded = ujson.dumps(test_float2)
print(f"Encoded: {encoded}")
decoded = ujson.loads(encoded)
print(f"Decoded: {decoded}")
print(f"Decoded is inf? {decoded == float('inf')}")

# Try to re-encode the decoded value
try:
    re_encoded = ujson.dumps(decoded)
    print(f"Re-encoded: {re_encoded}")
except Exception as e:
    print(f"ERROR on re-encode: {e}")

# Compare with standard json
json_encoded = json.dumps(test_float2)
json_decoded = json.loads(json_encoded) 
print(f"\nStandard json handles it: encoded={json_encoded}, decoded={json_decoded}")
print(f"Standard json preserves finiteness? {json_decoded != float('inf')}")
print()

print("=== Bug 4: Precision Loss in JSON Compatibility ===")
# This value loses precision when ujson decodes json output
test_float3 = 1.1447878645095912e+16
print(f"Original value: {test_float3}")

# Standard json encodes it
json_encoded = json.dumps([test_float3])
print(f"JSON encoded: {json_encoded}")

# ujson decodes it with precision loss
ujson_decoded = ujson.loads(json_encoded)
print(f"ujson decoded: {ujson_decoded[0]}")
print(f"Values equal? {ujson_decoded[0] == test_float3}")
print(f"Precision lost: {abs(ujson_decoded[0] - test_float3)}")

# Standard json preserves it
json_decoded = json.loads(json_encoded)
print(f"Standard json decoded: {json_decoded[0]}")
print(f"Standard json preserves? {json_decoded[0] == test_float3}")