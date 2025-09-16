#!/usr/bin/env python3
"""
Run the property-based tests for limits.aio
"""

import sys
import traceback

# Import the test module
import test_limits_aio_properties as test_module

def main():
    tests = [
        ("test_fixed_window_test_hit_consistency", test_module.test_fixed_window_test_hit_consistency),
        ("test_remaining_never_negative", test_module.test_remaining_never_negative),
        ("test_cost_exceeds_limit_always_fails", test_module.test_cost_exceeds_limit_always_fails),
        ("test_fixed_window_boundary_calculation", test_module.test_fixed_window_boundary_calculation),
        ("test_clear_resets_limit", test_module.test_clear_resets_limit),
        ("test_sliding_window_weighted_count", test_module.test_sliding_window_weighted_count),
        ("test_moving_window_acquire_consistency", test_module.test_moving_window_acquire_consistency),
        ("test_cross_strategy_first_hit", test_module.test_cross_strategy_first_hit)
    ]
    
    failed_tests = []
    
    for name, test in tests:
        print(f"\n{'='*60}")
        print(f"Running {name}...")
        print(f"{'='*60}")
        try:
            test()
            print(f"✓ {name} PASSED")
        except AssertionError as e:
            print(f"✗ {name} FAILED")
            print(f"Error: {e}")
            print(f"Traceback:")
            traceback.print_exc()
            failed_tests.append((name, e))
        except Exception as e:
            print(f"✗ {name} ERROR")
            print(f"Unexpected error: {e}")
            traceback.print_exc()
            failed_tests.append((name, e))
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if failed_tests:
        print(f"Failed tests: {len(failed_tests)}/{len(tests)}")
        for name, error in failed_tests:
            print(f"  - {name}: {str(error)[:100]}")
    else:
        print(f"All {len(tests)} tests passed!")
    
    return 0 if not failed_tests else 1

if __name__ == "__main__":
    sys.exit(main())