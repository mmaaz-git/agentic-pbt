#!/usr/bin/env /root/hypothesis-llm/envs/yq_env/bin/python3
"""Run property-based tests for yq.dumper"""

import sys
import traceback
from test_yq_dumper import *

def run_test(test_func, test_name):
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

tests = [
    (test_dumper_does_not_crash, "test_dumper_does_not_crash"),
    (test_dumper_with_options, "test_dumper_with_options"),
    (test_annotation_filtering_dicts, "test_annotation_filtering_dicts"),
    (test_annotation_filtering_lists, "test_annotation_filtering_lists"),
    (test_hash_key_consistency, "test_hash_key_consistency"),
    (test_hash_key_uniqueness, "test_hash_key_uniqueness"),
    (test_round_trip_simple, "test_round_trip_simple"),
    (test_dumper_idempotence, "test_dumper_idempotence"),
    (test_indentless_option_effect, "test_indentless_option_effect"),
    (test_alias_key_handling, "test_alias_key_handling"),
]

passed = 0
failed = 0

for test_func, test_name in tests:
    if run_test(test_func, test_name):
        passed += 1
    else:
        failed += 1

print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed")

if failed > 0:
    sys.exit(1)