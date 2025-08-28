#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import json
import math
from sudachipy import Config

print("=== Testing JSON spec compliance ===")

# Create configs with problematic values
config_nan = Config(projection=float('nan'))
config_inf = Config(projection=float('inf'))
config_neg_inf = Config(projection=float('-inf'))

# Get JSON strings
json_nan = config_nan.as_jsons()
json_inf = config_inf.as_jsons()
json_neg_inf = config_neg_inf.as_jsons()

print(f"JSON with NaN: {json_nan}")
print(f"JSON with Infinity: {json_inf}")
print(f"JSON with -Infinity: {json_neg_inf}")

# Test with standard JSON decoder (strict mode)
print("\n=== Testing with strict JSON decoder ===")
import json as strict_json

test_cases = [
    ("NaN", json_nan),
    ("Infinity", json_inf),
    ("-Infinity", json_neg_inf),
]

for name, json_str in test_cases:
    print(f"\nTesting {name}:")
    print(f"  JSON string: {json_str}")
    
    # Test with Python's default json (which allows NaN/Infinity)
    try:
        parsed = json.loads(json_str)
        print(f"  Python json.loads(): Success - {parsed}")
    except ValueError as e:
        print(f"  Python json.loads(): Failed - {e}")
    
    # Test with strict mode (disallow NaN/Infinity)
    try:
        parsed_strict = json.loads(json_str, allow_nan=False)
        print(f"  json.loads(allow_nan=False): Success - {parsed_strict}")
    except ValueError as e:
        print(f"  json.loads(allow_nan=False): Failed - {e}")
    
    # Test if other JSON parsers would accept it
    # Most JSON parsers in other languages don't accept NaN/Infinity
    print(f"  Valid JSON according to spec: {'No' if name in ['NaN', 'Infinity', '-Infinity'] else 'Yes'}")

print("\n=== Impact Analysis ===")
print("1. The JSON produced is not valid according to JSON spec (RFC 7159)")
print("2. It will fail when parsed by strict JSON parsers")
print("3. It will fail when transmitted to systems that use standard JSON")
print("4. JavaScript's JSON.parse() would fail on this output")
print("5. Many web APIs would reject this JSON")