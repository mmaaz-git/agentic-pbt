#!/usr/bin/env python3
"""Simple test runner for property-based tests."""

import sys
import traceback

# Add the troposphere environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import test functions
from test_identitystore_properties import (
    test_group_creation_and_serialization,
    test_group_membership_creation_and_validation,
    test_required_properties_validation,
    test_invalid_title_validation,
    test_type_validation_for_string_properties,
    test_equality_property,
    test_member_id_property_serialization,
    test_no_validation_mode
)

def run_test(test_func, test_name):
    """Run a single test function."""
    print(f"\nRunning {test_name}...")
    try:
        # Run the test with Hypothesis
        test_func()
        print(f"✓ {test_name} passed")
        return True
    except Exception as e:
        print(f"✗ {test_name} failed:")
        print(f"  Error: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    tests = [
        (test_group_creation_and_serialization, "test_group_creation_and_serialization"),
        (test_group_membership_creation_and_validation, "test_group_membership_creation_and_validation"),
        (test_required_properties_validation, "test_required_properties_validation"),
        (test_invalid_title_validation, "test_invalid_title_validation"),
        (test_type_validation_for_string_properties, "test_type_validation_for_string_properties"),
        (test_equality_property, "test_equality_property"),
        (test_member_id_property_serialization, "test_member_id_property_serialization"),
        (test_no_validation_mode, "test_no_validation_mode"),
    ]
    
    passed = 0
    failed = 0
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        sys.exit(1)