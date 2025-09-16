#!/usr/bin/env python3
"""Run the property-based tests."""

import sys
import traceback

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import test functions
from test_oam_properties import *

def run_single_test(test_func, test_name):
    """Run a single test and report results."""
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
    """Run all tests."""
    tests = [
        (test_linkfilter_round_trip, "test_linkfilter_round_trip"),
        (test_linkconfiguration_round_trip, "test_linkconfiguration_round_trip"),
        (test_link_round_trip, "test_link_round_trip"),
        (test_sink_round_trip, "test_sink_round_trip"),
        (test_link_required_fields_validation, "test_link_required_fields_validation"),
        (test_sink_required_fields_validation, "test_sink_required_fields_validation"),
        (test_title_validation, "test_title_validation"),
        (test_link_equality, "test_link_equality"),
        (test_link_resource_types_type_validation, "test_link_resource_types_type_validation"),
        (test_linkfilter_required_field, "test_linkfilter_required_field"),
        (test_link_with_configuration_round_trip, "test_link_with_configuration_round_trip"),
    ]
    
    passed = 0
    failed = 0
    
    print("Starting property-based tests for troposphere.oam...")
    print("=" * 60)
    
    for test_func, test_name in tests:
        if run_single_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()