#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import sudachipy
from sudachipy import Dictionary, SplitMode, Config

print("=== Testing what's possible without a dictionary ===")

# Test 1: Config object properties
print("\n1. Config object:")
config = Config()
print(f"   Default projection: {config.projection}")
print(f"   Can convert to JSON: {type(config.as_jsons())}")

# Test 2: SplitMode 
print("\n2. SplitMode:")
print(f"   SplitMode.A: {SplitMode.A}")
print(f"   SplitMode.B: {SplitMode.B}")
print(f"   SplitMode.C: {SplitMode.C}")

# Test if we can create SplitMode from string
try:
    mode_a = SplitMode("A")
    mode_b = SplitMode("b")  # lowercase
    print("   Can create SplitMode from strings")
except Exception as e:
    print(f"   Error creating SplitMode: {e}")

# Test 3: Try to create Dictionary without dict file
print("\n3. Dictionary creation without dict file:")
try:
    # Try with empty config
    dict_obj = Dictionary(config=Config())
    print("   Created dictionary with empty config")
except Exception as e:
    print(f"   Error: {e}")

# Test 4: Check if we can test error handling
print("\n4. Error handling tests:")
try:
    # Try invalid dict_type
    dict_obj = Dictionary(dict_type="invalid")
except ValueError as e:
    print(f"   Correctly raised ValueError for invalid dict_type: {e}")
except Exception as e:
    print(f"   Other error: {e}")

# Test 5: Config validation
print("\n5. Config properties that can be tested:")
config = Config()
config_with_system = Config(system="small")
config_with_projection = Config(projection="normalized")

print(f"   Config with system='small': {config_with_system.system}")
print(f"   Config with projection='normalized': {config_with_projection.projection}")

# Test valid projection values
valid_projections = ["surface", "normalized", "reading", "dictionary", 
                     "dictionary_and_surface", "normalized_and_surface", "normalized_nouns"]
print(f"   Valid projection values (from docs): {valid_projections}")