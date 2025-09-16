#!/usr/bin/env python3
"""Run property-based tests for troposphere.codeconnections"""

import sys
import os

# Add the virtual env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import and run the tests
import test_codeconnections_properties

# Run each test function manually to get detailed output
from hypothesis import settings
import traceback

test_functions = [
    test_codeconnections_properties.test_connection_round_trip,
    test_codeconnections_properties.test_connection_required_property_validation,
    test_codeconnections_properties.test_connection_title_validation,
    test_codeconnections_properties.test_tags_concatenation,
    test_codeconnections_properties.test_connection_type_validation,
    test_codeconnections_properties.test_connection_tags_type_validation,
    test_codeconnections_properties.test_connection_properties_preservation,
    test_codeconnections_properties.test_tags_handles_non_string_keys,
]

print("Running property-based tests for troposphere.codeconnections...")
print("=" * 60)

failures = []
for test_func in test_functions:
    test_name = test_func.__name__
    print(f"\nRunning {test_name}...")
    try:
        # Run with more examples to find bugs
        with settings(max_examples=100):
            test_func()
        print(f"✓ {test_name} passed")
    except Exception as e:
        print(f"✗ {test_name} FAILED")
        print(f"  Error: {e}")
        traceback.print_exc()
        failures.append((test_name, e))

print("\n" + "=" * 60)
if failures:
    print(f"\n{len(failures)} test(s) failed:")
    for name, error in failures:
        print(f"  - {name}: {error}")
else:
    print("\nAll tests passed!")