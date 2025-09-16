#!/usr/bin/env python3
"""Simple test runner for optax.losses property tests."""

import sys
import traceback
from test_optax_losses_properties import *

def run_test(test_func, test_name):
    """Run a single test and report results."""
    print(f"\nRunning {test_name}...", end=" ")
    try:
        test_func()
        print("✓ PASSED")
        return True
    except Exception as e:
        print("✗ FAILED")
        print(f"  Error: {e}")
        traceback.print_exc()
        return False

def main():
    tests = [
        (test_l2_loss_is_half_squared_error, "l2_loss = 0.5 * squared_error"),
        (test_cosine_distance_similarity_relationship, "cosine_distance = 1 - cosine_similarity"),
        (test_cosine_self_similarity, "cosine_similarity(x, x) = 1"),
        (test_squared_error_identity, "squared_error(x, x) = 0"),
        (test_squared_error_none_targets, "squared_error with None targets"),
        (test_huber_loss_properties, "huber_loss properties"),
        (test_hinge_loss_non_negative, "hinge_loss non-negative"),
        (test_log_cosh_properties, "log_cosh approximations"),
        (test_triplet_margin_loss_zero_condition, "triplet_margin_loss zero condition"),
        (test_weighted_logsoftmax_zero_weight_convention, "weighted_logsoftmax 0*log(0) = 0"),
    ]
    
    passed = 0
    failed = 0
    
    print("=" * 60)
    print("Running property-based tests for optax.losses")
    print("=" * 60)
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())