#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import sudachipy
from sudachipy import SplitMode, Config, errors

# Test SplitMode
print("=== SplitMode Tests ===")

# Test creation from strings
try:
    mode_a = SplitMode("A")
    mode_b = SplitMode("b")
    mode_c = SplitMode("C")
    mode_lower_a = SplitMode("a")
    print(f"SplitMode('A') == SplitMode.A: {mode_a == SplitMode.A}")
    print(f"SplitMode('a') == SplitMode.A: {mode_lower_a == SplitMode.A}")
    print(f"SplitMode('b') == SplitMode.B: {mode_b == SplitMode.B}")
except Exception as e:
    print(f"Error testing SplitMode: {e}")

# Test invalid modes
print("\nTesting invalid SplitMode inputs:")
for invalid in ["D", "1", "", None, "ABC"]:
    try:
        result = SplitMode(invalid)
        print(f"  SplitMode({repr(invalid)}) = {result} (unexpected success)")
    except Exception as e:
        print(f"  SplitMode({repr(invalid)}) raised {type(e).__name__}: {e}")

# Test Config
print("\n=== Config Tests ===")
config = Config()
print(f"Default config system: {config.system}")
print(f"Default config projection: {config.projection}")

# Test Config update
updated = config.update(system="test", projection="reading")
print(f"Updated system: {updated.system}")
print(f"Updated projection: {updated.projection}")

# Test Config JSON serialization
json_str = config.as_jsons()
print(f"Config as JSON (length): {len(json_str)}")

# Test _find_dict_path
print("\n=== _find_dict_path Tests ===")
for dict_type in ['small', 'core', 'full', 'invalid']:
    try:
        result = sudachipy._find_dict_path(dict_type)
        print(f"  _find_dict_path('{dict_type}') = {result}")
    except ValueError as e:
        print(f"  _find_dict_path('{dict_type}') raised ValueError: {e}")
    except ModuleNotFoundError as e:
        print(f"  _find_dict_path('{dict_type}') raised ModuleNotFoundError")

# Test Dictionary creation with various configs
print("\n=== Dictionary Creation Tests ===")
test_configs = [
    {},
    {"dict_type": "small"},
    {"dict": "/nonexistent/path.dic"},
    {"config": Config(system="core")},
]

for i, kwargs in enumerate(test_configs):
    try:
        dict_obj = sudachipy.Dictionary(**kwargs)
        print(f"  Test {i}: Success - {kwargs}")
    except Exception as e:
        print(f"  Test {i}: {type(e).__name__} - {kwargs}")