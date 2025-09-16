#!/usr/bin/env python3
"""Runner script for property-based tests."""

import sys
import traceback

# Import the test file
import test_google_oauth2_properties as tests

def run_test(test_func, test_name):
    """Run a single test function."""
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

def main():
    # List of tests to run
    test_cases = [
        (tests.test_basic_auth_base64_round_trip, "test_basic_auth_base64_round_trip"),
        (tests.test_sts_options_encoding_round_trip, "test_sts_options_encoding_round_trip"),
        (tests.test_expiry_parsing_int_and_string, "test_expiry_parsing_int_and_string"),
        (tests.test_sts_empty_field_removal, "test_sts_empty_field_removal"),
        (tests.test_error_response_parsing_json, "test_error_response_parsing_json"),
        (tests.test_error_response_parsing_fallback, "test_error_response_parsing_fallback"),
    ]
    
    results = []
    for test_func, test_name in test_cases:
        result = run_test(test_func, test_name)
        results.append((test_name, result))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} tests")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())