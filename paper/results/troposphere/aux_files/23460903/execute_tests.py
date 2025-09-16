#!/usr/bin/env python3
"""Execute the property-based tests and report results"""

import sys
import traceback

# Add the environment path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import the test functions
from test_iotcoredeviceadvisor import (
    test_device_under_test_roundtrip,
    test_suite_definition_config_required_fields,
    test_boolean_validator,
    test_suite_definition_title_validation,
    test_suite_definition_complex_serialization,
    test_suite_config_devices_type_validation
)

def run_single_test(test_func, test_name):
    """Run a single property test and report results"""
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print('='*60)
    
    try:
        # Hypothesis tests run their own loop internally
        test_func()
        print(f"✓ {test_name} PASSED")
        return True
    except AssertionError as e:
        print(f"✗ {test_name} FAILED")
        print(f"Assertion Error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ {test_name} ERROR")
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests and report summary"""
    tests = [
        (test_device_under_test_roundtrip, "DeviceUnderTest round-trip serialization"),
        (test_suite_definition_config_required_fields, "SuiteDefinitionConfiguration required fields validation"),
        (test_boolean_validator, "Boolean validator edge cases"),
        (test_suite_definition_title_validation, "SuiteDefinition title validation"),
        (test_suite_definition_complex_serialization, "Complex nested object serialization"),
        (test_suite_config_devices_type_validation, "Devices field type validation"),
    ]
    
    results = []
    
    print("Starting property-based testing for troposphere.iotcoredeviceadvisor")
    
    for test_func, test_name in tests:
        passed = run_single_test(test_func, test_name)
        results.append((test_name, passed))
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count < total_count:
        print("\nSome tests failed. Investigate the failures above.")
        return 1
    else:
        print("\nAll tests passed successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(main())