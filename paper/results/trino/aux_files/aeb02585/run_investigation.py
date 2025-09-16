#!/usr/bin/env python3
"""Run investigation tests for trino.types."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

import traceback
from test_trino_investigation import *

# List of test functions to run
tests = [
    test_time_overflow_at_midnight,
    test_time_round_to_ordering,
    test_fraction_to_decimal_single_zero,
    test_fraction_to_decimal_max_values,
    test_namedrowtuple_getattr_with_count_method,
    test_namedrowtuple_with_python_keywords,
    test_time_with_nan_fraction,
    test_time_with_inf_fraction,
    test_time_round_to_with_special_decimal,
    test_time_microsecond_overflow,
    test_time_round_to_negative_precision,
]

print("Running investigation tests for trino.types...")
print("=" * 60)

failed_tests = []
passed_tests = []

for test_func in tests:
    test_name = test_func.__name__
    print(f"\nRunning {test_name}...")
    try:
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