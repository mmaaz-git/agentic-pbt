#!/usr/bin/env python3
"""Run the property-based tests for trino.types."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

import traceback
from test_trino_types import *

# List of test functions to run
tests = [
    test_time_round_to_precision_bounds,
    test_time_add_time_delta_preserves_timezone,
    test_timewithtz_add_time_delta_preserves_timezone,
    test_timestamp_round_to_precision_bounds,
    test_timestampwithtz_add_time_delta_preserves_timezone,
    test_namedrowtuple_unique_name_access,
    test_namedrowtuple_duplicate_name_raises_error,
    test_namedrowtuple_is_tuple,
    test_fraction_to_decimal_basic,
    test_fraction_to_decimal_range,
    test_time_round_to_idempotent,
    test_time_to_python_type_with_zero_fraction,
    test_timestamp_to_python_type_with_zero_fraction,
]

print("Running property-based tests for trino.types...")
print("=" * 60)

failed_tests = []
passed_tests = []

for test_func in tests:
    test_name = test_func.__name__
    print(f"\nRunning {test_name}...")
    try:
        # Hypothesis tests are decorated, so we just call them
        test_func()
        print(f"✓ {test_name} PASSED")
        passed_tests.append(test_name)
    except Exception as e:
        print(f"✗ {test_name} FAILED")
        print(f"Error: {e}")
        print(traceback.format_exc())
        failed_tests.append((test_name, e, traceback.format_exc()))

print("\n" + "=" * 60)
print(f"Results: {len(passed_tests)} passed, {len(failed_tests)} failed")

if failed_tests:
    print("\nFailed tests:")
    for test_name, error, tb in failed_tests:
        print(f"\n{test_name}:")
        print(f"  Error: {error}")
        if hasattr(error, '__notes__'):
            for note in error.__notes__:
                print(f"  Note: {note}")
else:
    print("\nAll tests passed! ✅")