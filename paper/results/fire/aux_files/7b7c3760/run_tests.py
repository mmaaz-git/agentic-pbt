#!/usr/bin/env python3
"""Run the property-based tests for fire.inspectutils."""

import sys
import traceback

# Add fire_env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

# Import test file
import test_inspectutils_properties as tests

# Run tests manually
def run_test(test_func, test_name):
    print(f"\nRunning {test_name}...")
    try:
        test_func()
        print(f"  ✓ {test_name} passed")
        return True
    except Exception as e:
        print(f"  ✗ {test_name} failed:")
        print(f"    {e}")
        traceback.print_exc()
        return False

# List of test functions to run
test_functions = [
    (tests.test_getfullargspec_returns_fullargspec, "test_getfullargspec_returns_fullargspec"),
    (tests.test_getfullargspec_defaults_correspondence, "test_getfullargspec_defaults_correspondence"),
    (tests.test_isnamedtuple_consistency, "test_isnamedtuple_consistency"),
    (tests.test_isnamedtuple_with_real_namedtuples, "test_isnamedtuple_with_real_namedtuples"),
    (tests.test_info_returns_dict_with_required_fields, "test_info_returns_dict_with_required_fields"),
    (tests.test_getfileandline_invariants, "test_getfileandline_invariants"),
    (tests.test_getclassattrsdict_properties, "test_getclassattrsdict_properties"),
    (tests.test_iscoroutinefunction_no_crash, "test_iscoroutinefunction_no_crash"),
    (tests.test_getfullargspec_deterministic, "test_getfullargspec_deterministic"),
    (tests.test_fullargspec_constructor, "test_fullargspec_constructor"),
]

print("Starting property-based testing of fire.inspectutils...")
passed = 0
failed = 0

for test_func, test_name in test_functions:
    if run_test(test_func, test_name):
        passed += 1
    else:
        failed += 1

print(f"\n{'='*60}")
print(f"Results: {passed} passed, {failed} failed")

if failed == 0:
    print("All tests passed! ✅")
else:
    print(f"Some tests failed. Please review the errors above.")