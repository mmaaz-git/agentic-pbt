#!/usr/bin/env python3
"""Run the property-based tests for Hungarian algorithm."""

import sys
import os

# Add the virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

# Now run the tests
from test_hungarian_properties import *

if __name__ == "__main__":
    print("Running property-based tests for optax.assignment...")
    
    # Run each test function
    test_functions = [
        test_two_implementations_same_cost,
        test_assignment_count_invariant,
        test_unique_assignments,
        test_transpose_property,
        test_deterministic_cost,
        test_inf_handling,
        test_zero_cost_optimal,
        test_base_vs_optimized_consistency
    ]
    
    for test_func in test_functions:
        print(f"\nRunning {test_func.__name__}...")
        try:
            test_func()
            print(f"✓ {test_func.__name__} passed")
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            import traceback
            traceback.print_exc()