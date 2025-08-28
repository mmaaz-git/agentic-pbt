#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import json
import math
from sudachipy import Config

print("=== Bug Reproduction: Config accepts non-string values for projection ===\n")

# Demonstrate the bug
print("1. Config accepts float('nan') for projection field:")
config = Config(projection=float('nan'))
print(f"   config = Config(projection=float('nan'))")
print(f"   config.projection = {config.projection}")
print(f"   type(config.projection) = {type(config.projection)}")

print("\n2. This produces invalid JSON:")
json_str = config.as_jsons()
print(f"   config.as_jsons() = {repr(json_str)}")

print("\n3. The JSON is not compliant with JSON spec (RFC 7159):")
print("   NaN, Infinity, and -Infinity are not valid JSON values")

print("\n4. Attempting to serialize with strict JSON fails:")
try:
    # This would fail if we try to create strict JSON
    strict_json = json.dumps({"projection": float('nan')}, allow_nan=False)
except ValueError as e:
    print(f"   json.dumps({{'projection': float('nan')}}, allow_nan=False)")
    print(f"   Raises ValueError: {e}")

print("\n5. Type contract violation:")
print("   According to sudachipy.pyi, projection should be str")
print("   Valid values: 'surface', 'normalized', 'reading', 'dictionary',")
print("                 'dictionary_and_surface', 'normalized_and_surface', 'normalized_nouns'")
print("   But Config accepts any type without validation")

print("\n6. Additional problematic values accepted:")
test_values = [float('inf'), float('-inf'), 123, True, [1,2,3], {"key": "value"}]
for val in test_values:
    c = Config(projection=val)
    print(f"   Config(projection={repr(val)}) -> projection={c.projection} (type: {type(c.projection).__name__})")