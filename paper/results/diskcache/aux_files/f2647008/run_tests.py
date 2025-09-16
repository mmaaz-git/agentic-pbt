#!/usr/bin/env python
"""Run the property-based tests manually."""

import sys
import traceback
from hypothesis import given, strategies as st, settings, Verbosity

# Import all test functions
from test_fanout_properties import (
    test_sharding_consistency,
    test_set_get_round_trip,
    test_incr_decr_inverse,
    test_stats_consistency,
    test_contains_get_consistency,
    test_add_idempotence,
    test_length_consistency,
    test_iteration_consistency,
    test_pop_consistency,
    test_clear_removes_all,
)

def run_test(test_func, name):
    """Run a single test function and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print('='*60)
    
    try:
        # Run the test with more examples
        with settings(max_examples=100, verbosity=Verbosity.verbose):
            test_func()
        print(f"✓ {name} PASSED")
        return True
    except Exception as e:
        print(f"✗ {name} FAILED")
        print(f"Error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    tests = [
        (test_sharding_consistency, "test_sharding_consistency"),
        (test_set_get_round_trip, "test_set_get_round_trip"),
        (test_incr_decr_inverse, "test_incr_decr_inverse"),
        (test_stats_consistency, "test_stats_consistency"),
        (test_contains_get_consistency, "test_contains_get_consistency"),
        (test_add_idempotence, "test_add_idempotence"),
        (test_length_consistency, "test_length_consistency"),
        (test_iteration_consistency, "test_iteration_consistency"),
        (test_pop_consistency, "test_pop_consistency"),
        (test_clear_removes_all, "test_clear_removes_all"),
    ]
    
    passed = 0
    failed = 0
    
    for test_func, name in tests:
        if run_test(test_func, name):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print('='*60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())