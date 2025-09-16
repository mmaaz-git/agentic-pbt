#!/usr/bin/env python3
import sys
import traceback

# Add site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/sqltrie_env/lib/python3.13/site-packages')

from test_sqltrie_edge_cases import *
from hypothesis import given, settings, strategies as st
import hypothesis

# Configure hypothesis
hypothesis.settings.register_profile("dev", max_examples=30, deadline=None)
hypothesis.settings.load_profile("dev")

def run_test(test_func, test_name):
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print('='*60)
    try:
        test_func()
        print(f"✓ {test_name} passed")
        return True
    except Exception as e:
        print(f"✗ {test_name} failed")
        print(f"Error: {e}")
        traceback.print_exc()
        return False

# Run each test
tests = [
    (test_empty_key_handling, "test_empty_key_handling"),
    (test_hierarchical_deletion, "test_hierarchical_deletion"),
    (test_json_trie_serialization, "test_json_trie_serialization"),
    (test_concurrent_modifications, "test_concurrent_modifications"),
    (test_view_with_nonexistent_prefix, "test_view_with_nonexistent_prefix"),
    (test_ls_consistency, "test_ls_consistency"),
    (test_special_characters_in_keys, "test_special_characters_in_keys"),
    (test_transaction_rollback, "test_transaction_rollback"),
]

results = []
for test_func, test_name in tests:
    result = run_test(test_func, test_name)
    results.append((test_name, result))

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
for test_name, result in results:
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"{status}: {test_name}")