#!/usr/bin/env python3
"""Verbose test runner showing Hypothesis execution details"""

import sys
import os

# Add the yq_env site-packages to Python path
site_packages_path = "/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages"
if site_packages_path not in sys.path:
    sys.path.insert(0, site_packages_path)

# Import required modules
from hypothesis import given, settings, Verbosity
from hypothesis.reporting import default

if __name__ == "__main__":
    try:
        # Set Hypothesis to be more verbose
        settings.register_profile("verbose", settings(verbosity=Verbosity.verbose))
        settings.load_profile("verbose")
        
        import test_yq_dumper
        print("=" * 70)
        print("Running property-based tests with Hypothesis - VERBOSE MODE")
        print("=" * 70)
        print("This will show detailed information about test case generation")
        print("and execution. Hypothesis will generate many test cases automatically.")
        print("=" * 70)
        
        # Get all test functions
        test_functions = [
            ("test_dumper_does_not_crash", test_yq_dumper.test_dumper_does_not_crash),
            ("test_dumper_with_options", test_yq_dumper.test_dumper_with_options), 
            ("test_annotation_filtering_dicts", test_yq_dumper.test_annotation_filtering_dicts),
            ("test_hash_key_consistency", test_yq_dumper.test_hash_key_consistency),
            ("test_round_trip_simple", test_yq_dumper.test_round_trip_simple),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in test_functions:
            print(f"\n{'─' * 60}")
            print(f"Running {test_name} with property-based testing...")
            print("Hypothesis will generate and test multiple examples:")
            try:
                test_func()
                print(f"✓ {test_name} PASSED - All generated test cases passed")
                passed += 1
            except Exception as e:
                print(f"✗ {test_name} FAILED:")
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
                
        print(f"\n{'=' * 70}")
        print(f"COMPREHENSIVE TEST RESULTS")
        print(f"{'=' * 70}")
        print(f"Tests executed: {passed + failed}")
        print(f"Passed: {passed}")  
        print(f"Failed: {failed}")
        print(f"Success rate: {(passed / (passed + failed) * 100):.1f}%" if (passed + failed) > 0 else "N/A")
        print("\nNote: Each test above involved Hypothesis generating many")
        print("random test cases to thoroughly exercise the code under test.")
        
        if failed > 0:
            print("\nSome property-based tests failed. See output above for details.")
            sys.exit(1)
        else:
            print("\nAll property-based tests passed! The yq.dumper module")
            print("appears to be robust across a wide range of inputs.")
            
    except ImportError as e:
        print(f"Import error: {e}")
        print("Failed to import required modules")
        sys.exit(1)