#!/usr/bin/env python3
"""Run property-based tests for isort.api module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from test_isort_api_properties import *

print("Running property-based tests for isort.api...")
print("=" * 60)

# Run each test function
test_functions = [
    ("Idempotence", test_sort_idempotence),
    ("Check-Sort Consistency", test_check_sort_consistency),
    ("Import Preservation", test_import_preservation),
    ("ImportKey Uniqueness", test_import_key_uniqueness),
    ("Show Diff Consistency", test_show_diff_consistency),
    ("Empty/Whitespace Handling", test_empty_and_whitespace),
    ("Extension Handling", test_extension_handling),
    ("Config Kwargs", test_config_kwargs),
]

for name, test_func in test_functions:
    print(f"\nTesting {name}...")
    try:
        test_func()
        print(f"✓ {name} passed")
    except AssertionError as e:
        print(f"✗ {name} FAILED:")
        print(f"  {e}")
    except Exception as e:
        print(f"✗ {name} ERROR:")
        print(f"  {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("Testing complete!")