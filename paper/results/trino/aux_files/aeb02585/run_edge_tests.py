#!/usr/bin/env python3
"""Run the edge case property-based tests for trino.types."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

import traceback
from test_trino_types_edge_cases import *

# List of test functions to run
tests = [
    test_time_round_to_with_near_one_second_fraction,
    test_timestamp_round_to_at_day_boundary,
    test_namedrowtuple_getattr_nonexistent_duplicate,
    test_fraction_to_decimal_empty_string,
    test_fraction_to_decimal_leading_zeros,
    test_time_new_instance_creates_new_object,
    test_time_round_to_zero_precision,
    test_time_high_precision_fraction_handling,
    test_namedrowtuple_with_all_none_names,
    test_namedrowtuple_annotations,
    test_namedrowtuple_getnewargs,
    test_namedrowtuple_state,
]

print("Running edge case property-based tests for trino.types...")
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