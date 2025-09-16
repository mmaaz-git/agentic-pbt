#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import math
import json
from sudachipy import Config

# Test 1: Config accepts float NaN for projection field
print("=== Testing Config with NaN ===")
nan_val = float('nan')
config = Config(projection=nan_val)
print(f"Config created with projection=NaN: {config}")
print(f"config.projection: {config.projection}")
print(f"Type of projection: {type(config.projection)}")
print(f"Is NaN: {math.isnan(config.projection)}")

# Test 2: Can we serialize this to JSON?
print("\n=== Testing JSON serialization with NaN ===")
try:
    json_str = config.as_jsons()
    print(f"JSON string: {json_str}")
    
    # Try to parse it back
    parsed = json.loads(json_str)
    print(f"Parsed JSON: {parsed}")
except (ValueError, TypeError) as e:
    print(f"JSON serialization failed: {e}")

# Test 3: Test with infinity
print("\n=== Testing Config with Infinity ===")
inf_val = float('inf')
config_inf = Config(projection=inf_val)
print(f"Config created with projection=inf: {config_inf}")

try:
    json_str_inf = config_inf.as_jsons()
    print(f"JSON string with inf: {json_str_inf}")
    parsed_inf = json.loads(json_str_inf)
    print(f"Parsed JSON: {parsed_inf}")
except (ValueError, TypeError) as e:
    print(f"JSON serialization failed: {e}")

# Test 4: Test with regular float
print("\n=== Testing Config with regular float ===")
config_float = Config(projection=3.14)
print(f"Config created with projection=3.14: {config_float}")
print(f"Type of projection: {type(config_float.projection)}")

json_str_float = config_float.as_jsons()
print(f"JSON string: {json_str_float}")
parsed_float = json.loads(json_str_float)
print(f"Parsed JSON: {parsed_float}")

# Test 5: Test with other non-string types
print("\n=== Testing Config with other types ===")
test_values = [
    42,           # int
    True,         # bool
    None,         # None
    [1, 2, 3],    # list
    {"a": 1},     # dict
]

for val in test_values:
    try:
        config_test = Config(projection=val)
        print(f"Config(projection={repr(val)}): projection={config_test.projection}, type={type(config_test.projection)}")
        
        # Try JSON serialization
        json_test = config_test.as_jsons()
        parsed_test = json.loads(json_test)
        print(f"  JSON serialization successful: {parsed_test.get('projection')}")
    except Exception as e:
        print(f"Config(projection={repr(val)}): Failed with {type(e).__name__}: {e}")

# Test 6: Document the expected vs actual behavior
print("\n=== Expected vs Actual Behavior ===")
print("According to the type hints (sudachipy.pyi), projection should be a string.")
print("Valid values documented: 'surface', 'normalized', 'reading', 'dictionary',")
print("                         'dictionary_and_surface', 'normalized_and_surface', 'normalized_nouns'")
print("\nActual behavior: Config accepts any type for projection field")
print("This creates issues with:")
print("1. NaN values (NaN != NaN, breaking equality checks)")
print("2. JSON serialization (NaN and Infinity are not valid JSON)")
print("3. Type safety (accepts non-string values when strings are expected)")