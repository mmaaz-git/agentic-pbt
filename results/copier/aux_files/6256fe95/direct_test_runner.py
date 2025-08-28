#!/usr/bin/env python3
"""Direct test runner for copier._user_data property tests."""

import sys
import traceback

# Add the copier environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

# Import test module
from test_copier_user_data import *

def run_single_test(test_func, test_name):
    """Run a single property test and report results."""
    print(f"\nRunning {test_name}...")
    try:
        test_func()
        print(f"✓ {test_name} passed")
        return True
    except Exception as e:
        print(f"✗ {test_name} failed:")
        print(f"  Error: {e}")
        traceback.print_exc()
        return False

# List of test functions to run
tests = [
    (test_parse_yaml_string_round_trip, "test_parse_yaml_string_round_trip"),
    (test_parse_yaml_list_returns_list_or_raises, "test_parse_yaml_list_returns_list_or_raises"),
    (test_parse_yaml_list_preserves_items, "test_parse_yaml_list_preserves_items"),
    (test_answers_map_combined_contains_all, "test_answers_map_combined_contains_all"),
    (test_cast_str_to_native_idempotent, "test_cast_str_to_native_idempotent"),
    (test_question_type_casting_preserves_type, "test_question_type_casting_preserves_type"),
    (test_json_yaml_cast_round_trip, "test_json_yaml_cast_round_trip"),
]

print("Starting property-based testing of copier._user_data...")
print("=" * 60)

passed = 0
failed = 0

for test_func, test_name in tests:
    if run_single_test(test_func, test_name):
        passed += 1
    else:
        failed += 1

print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed")

if failed > 0:
    sys.exit(1)