#!/usr/bin/env python3
"""Runner script for the property-based tests"""

import sys
import traceback

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

# Import test module
import test_trino_constants

# Run each test function
test_functions = [
    test_trino_constants.test_client_capabilities_concatenation,
    test_trino_constants.test_header_name_pattern,
    test_trino_constants.test_scale_types_subset_of_precision_types,
    test_trino_constants.test_protocol_string_values,
    test_trino_constants.test_default_port_values,
    test_trino_constants.test_url_path_format,
    test_trino_constants.test_max_nt_password_size,
    test_trino_constants.test_type_lists_consistency,
    test_trino_constants.test_constants_immutability,
]

failed_tests = []
passed_tests = []

for test_func in test_functions:
    test_name = test_func.__name__
    print(f"Running {test_name}...")
    try:
        test_func()
        print(f"  ✓ {test_name} passed")
        passed_tests.append(test_name)
    except AssertionError as e:
        print(f"  ✗ {test_name} failed: {e}")
        failed_tests.append((test_name, str(e), traceback.format_exc()))
    except Exception as e:
        print(f"  ✗ {test_name} errored: {e}")
        failed_tests.append((test_name, str(e), traceback.format_exc()))

print(f"\n{'='*60}")
print(f"Test Results: {len(passed_tests)} passed, {len(failed_tests)} failed")
print(f"{'='*60}")

if failed_tests:
    print("\nFailed tests details:")
    for test_name, error_msg, tb in failed_tests:
        print(f"\n{test_name}:")
        print(f"  Error: {error_msg}")
        if "AssertionError" not in tb:
            print(f"  Traceback:\n{tb}")