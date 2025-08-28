#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import sudachipy
from sudachipy import SplitMode
import inspect

# Test components that don't require a dictionary file

print("=== Testing SplitMode ===")
# Test SplitMode creation
modes = [SplitMode.A, SplitMode.B, SplitMode.C]
for mode in modes:
    print(f"Mode: {mode}")

# Test SplitMode from string
test_strings = ["A", "a", "B", "b", "C", "c", None]
for s in test_strings:
    try:
        mode = SplitMode(s)
        print(f"SplitMode('{s}') created successfully")
    except Exception as e:
        print(f"SplitMode('{s}') failed: {e}")

# Test if we can access Config
print("\n=== Testing Config ===")
try:
    from sudachipy.config import Config
    print(f"Config class available: {Config}")
    print(f"Config attributes: {dir(Config)}")
except Exception as e:
    print(f"Could not import Config: {e}")

# Check for errors module
print("\n=== Testing errors module ===")
try:
    from sudachipy import errors
    print(f"Errors module: {errors}")
    print(f"Errors module attributes: {dir(errors)}")
except Exception as e:
    print(f"Could not import errors: {e}")