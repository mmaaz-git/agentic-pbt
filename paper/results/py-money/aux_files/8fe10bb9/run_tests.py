#!/usr/bin/env python3
"""Run property-based tests for the money module"""

import traceback
from test_money_properties import *

def run_test(test_func, test_name):
    """Run a single test and report results"""
    print(f"\nRunning {test_name}...")
    try:
        test_func()
        print(f"✓ {test_name} passed")
        return True
    except Exception as e:
        print(f"✗ {test_name} FAILED")
        print(f"  Error: {e}")
        traceback.print_exc()
        return False

# List of all tests
tests = [
    (test_sub_units_round_trip, "test_sub_units_round_trip"),
    (test_addition_commutative, "test_addition_commutative"),
    (test_addition_identity, "test_addition_identity"),
    (test_addition_inverse, "test_addition_inverse"),
    (test_absolute_value, "test_absolute_value"),
    (test_comparison_transitivity, "test_comparison_transitivity"),
    (test_total_ordering, "test_total_ordering"),
    (test_hash_consistency, "test_hash_consistency"),
    (test_multiplication_scalar, "test_multiplication_scalar"),
    (test_division_scalar, "test_division_scalar"),
    (test_division_by_money, "test_division_by_money"),
    (test_negation_self_inverse, "test_negation_self_inverse"),
    (test_boolean_conversion, "test_boolean_conversion"),
    (test_repr_format, "test_repr_format"),
]

# Run all tests
print("=" * 60)
print("Running property-based tests for money module")
print("=" * 60)

passed = 0
failed = 0

for test_func, test_name in tests:
    if run_test(test_func, test_name):
        passed += 1
    else:
        failed += 1

print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 60)