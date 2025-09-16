#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

# Import and run the tests
from test_htmldate_validators import *

if __name__ == "__main__":
    print("Running property-based tests for htmldate.validators...")
    
    tests = [
        ("test_convert_date_round_trip", test_convert_date_round_trip),
        ("test_is_valid_format_accepts_valid_formats", test_is_valid_format_accepts_valid_formats),
        ("test_is_valid_format_rejects_invalid_formats", test_is_valid_format_rejects_invalid_formats),
        ("test_is_valid_date_respects_bounds", test_is_valid_date_respects_bounds),
        ("test_check_date_input_iso_format", test_check_date_input_iso_format),
        ("test_check_date_input_returns_default_for_invalid", test_check_date_input_returns_default_for_invalid),
        ("test_get_min_date_returns_default_for_invalid", test_get_min_date_returns_default_for_invalid),
        ("test_get_max_date_returns_default_for_invalid", test_get_max_date_returns_default_for_invalid),
        ("test_validate_and_convert_consistency", test_validate_and_convert_consistency),
        ("test_convert_date_datetime_input", test_convert_date_datetime_input),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for test_name, test_func in tests:
        try:
            print(f"\nRunning {test_name}...")
            test_func()
            print(f"✓ {test_name} passed")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_name} failed: {e}")
            failed += 1
            errors.append((test_name, str(e)))
        except Exception as e:
            print(f"✗ {test_name} error: {e}")
            failed += 1
            errors.append((test_name, str(e)))
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    
    if errors:
        print("\nFailures:")
        for test_name, error in errors:
            print(f"  - {test_name}: {error}")