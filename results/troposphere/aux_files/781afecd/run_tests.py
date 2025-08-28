#!/usr/bin/env python3
"""Simple test runner for troposphere.elasticbeanstalk tests."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import traceback
from hypothesis import given, strategies as st, settings, Verbosity
from test_troposphere_elasticbeanstalk import *

# Configure Hypothesis
settings.register_profile("debug", max_examples=10, verbosity=Verbosity.verbose)
settings.load_profile("debug")

def run_test(test_func, test_name, *args):
    """Run a single test and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print('='*60)
    try:
        # For property-based tests, we need to run them through Hypothesis
        if hasattr(test_func, 'hypothesis'):
            # This is a Hypothesis test, run it properly
            test_func()
        else:
            # Regular test
            test_func(*args)
        print(f"✓ {test_name} PASSED")
        return True
    except Exception as e:
        print(f"✗ {test_name} FAILED")
        print(f"Error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests and report results."""
    print("Starting property-based tests for troposphere.elasticbeanstalk")
    
    passed = 0
    failed = 0
    
    # Test validator functions
    if run_test(test_validate_tier_name_invalid, "test_validate_tier_name_invalid"):
        passed += 1
    else:
        failed += 1
        
    if run_test(test_validate_tier_name_valid, "test_validate_tier_name_valid"):
        passed += 1
    else:
        failed += 1
        
    if run_test(test_validate_tier_type_invalid, "test_validate_tier_type_invalid"):
        passed += 1
    else:
        failed += 1
        
    if run_test(test_validate_tier_type_valid, "test_validate_tier_type_valid"):
        passed += 1
    else:
        failed += 1
    
    # Test title validation
    if run_test(test_title_validation, "test_title_validation"):
        passed += 1
    else:
        failed += 1
    
    # Test required properties
    if run_test(test_required_properties_application_version, "test_required_properties_application_version"):
        passed += 1
    else:
        failed += 1
        
    if run_test(test_source_bundle_required_properties, "test_source_bundle_required_properties"):
        passed += 1
    else:
        failed += 1
    
    # Test round-trip properties
    if run_test(test_application_round_trip, "test_application_round_trip"):
        passed += 1
    else:
        failed += 1
        
    if run_test(test_environment_round_trip, "test_environment_round_trip"):
        passed += 1
    else:
        failed += 1
    
    # Test other properties
    if run_test(test_tier_property, "test_tier_property"):
        passed += 1
    else:
        failed += 1
        
    if run_test(test_option_setting_properties, "test_option_setting_properties"):
        passed += 1
    else:
        failed += 1
        
    if run_test(test_list_property_type_validation, "test_list_property_type_validation"):
        passed += 1
    else:
        failed += 1
        
    if run_test(test_max_age_rule_properties, "test_max_age_rule_properties"):
        passed += 1
    else:
        failed += 1
        
    if run_test(test_max_count_rule_properties, "test_max_count_rule_properties"):
        passed += 1
    else:
        failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Investigating failures...")
        return 1
    else:
        print("\n✅ All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())