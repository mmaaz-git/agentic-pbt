#!/usr/bin/env python3
"""Run property-based tests for fixit.api module."""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, "/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages")

# Import test functions
from test_fixit_api import (
    test_print_result_return_value,
    test_lint_violation_autofixable,
    test_fixit_bytes_yields_result,
    test_result_invariants,
    test_config_path_resolution
)

def run_test(test_func, test_name, num_examples=100):
    """Run a single property test manually."""
    print(f"\nRunning {test_name}...")
    failures = []
    
    try:
        # Run the test multiple times with different examples
        for i in range(num_examples):
            try:
                test_func()
            except Exception as e:
                # Capture failures
                failures.append({
                    'example': i,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
                if len(failures) >= 3:  # Stop after a few failures
                    break
        
        if failures:
            print(f"  ❌ FAILED: {len(failures)} failures out of {i+1} examples")
            for fail in failures[:3]:  # Show first 3 failures
                print(f"    Example {fail['example']}: {fail['error']}")
            return False
        else:
            print(f"  ✅ PASSED: {num_examples} examples")
            return True
            
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Starting property-based testing of fixit.api module")
    print("=" * 60)
    
    tests = [
        (test_print_result_return_value, "print_result return value property"),
        (test_lint_violation_autofixable, "LintViolation.autofixable property"),
        (test_fixit_bytes_yields_result, "fixit_bytes yields result property"),
        (test_result_invariants, "Result object invariants"),
        (test_config_path_resolution, "Config path resolution property"),
    ]
    
    passed = 0
    failed = 0
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Summary: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n✅ All property tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed")