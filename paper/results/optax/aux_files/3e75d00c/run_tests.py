#!/usr/bin/env python3
"""Simple test runner for optax.contrib tests."""

import sys
import traceback

# Run each test function
from test_optax_contrib import (
    test_normalize_unit_norm,
    test_complex_to_real_round_trip,
    test_real_arrays_pass_through,
    test_split_real_imaginary_round_trip,
    test_reduce_on_plateau_validation,
    test_normalize_zero_gradient_stability
)

def run_test(test_func, test_name):
    """Run a single test function multiple times."""
    print(f"\nRunning {test_name}...")
    try:
        # Hypothesis tests run multiple examples internally
        test_func()
        print(f"✓ {test_name} passed")
        return True
    except Exception as e:
        print(f"✗ {test_name} failed:")
        print(f"  Error: {e}")
        traceback.print_exc()
        return False

def main():
    tests = [
        (test_normalize_unit_norm, "test_normalize_unit_norm"),
        (test_complex_to_real_round_trip, "test_complex_to_real_round_trip"),
        (test_real_arrays_pass_through, "test_real_arrays_pass_through"),
        (test_split_real_imaginary_round_trip, "test_split_real_imaginary_round_trip"),
        (test_reduce_on_plateau_validation, "test_reduce_on_plateau_validation"),
        (test_normalize_zero_gradient_stability, "test_normalize_zero_gradient_stability")
    ]
    
    passed = 0
    failed = 0
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()