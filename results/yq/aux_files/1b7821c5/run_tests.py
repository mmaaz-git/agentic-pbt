#!/usr/bin/env python3
"""Simple test runner with path setup"""

import sys
import os

# Add the yq_env site-packages to Python path
site_packages_path = "/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages"
if site_packages_path not in sys.path:
    sys.path.insert(0, site_packages_path)

# Now run the tests
if __name__ == "__main__":
    try:
        import test_yq_dumper
        print("=" * 60)
        print("Running comprehensive property-based tests for yq.dumper")
        print("=" * 60)
        
        # Import test functions from hypothesis
        from hypothesis import given, settings
        
        # Get all test functions
        test_functions = [
            ("test_dumper_does_not_crash", test_yq_dumper.test_dumper_does_not_crash),
            ("test_dumper_with_options", test_yq_dumper.test_dumper_with_options),
            ("test_annotation_filtering_dicts", test_yq_dumper.test_annotation_filtering_dicts),
            ("test_annotation_filtering_lists", test_yq_dumper.test_annotation_filtering_lists),
            ("test_hash_key_consistency", test_yq_dumper.test_hash_key_consistency),
            ("test_hash_key_uniqueness", test_yq_dumper.test_hash_key_uniqueness),
            ("test_round_trip_simple", test_yq_dumper.test_round_trip_simple),
            ("test_dumper_idempotence", test_yq_dumper.test_dumper_idempotence),
            ("test_indentless_option_effect", test_yq_dumper.test_indentless_option_effect),
            ("test_alias_key_handling", test_yq_dumper.test_alias_key_handling),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in test_functions:
            print(f"\n{'─' * 50}")
            print(f"Running {test_name}...")
            try:
                # Run the hypothesis test
                test_func()
                print(f"✓ {test_name} PASSED")
                passed += 1
            except Exception as e:
                print(f"✗ {test_name} FAILED:")
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
                
        print(f"\n{'=' * 60}")
        print(f"TEST RESULTS")
        print(f"{'=' * 60}")
        print(f"Total tests: {passed + failed}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {(passed / (passed + failed) * 100):.1f}%" if (passed + failed) > 0 else "N/A")
        
        if failed > 0:
            print("\nSome tests failed. See output above for details.")
            sys.exit(1)
        else:
            print("\nAll tests passed!")
            
    except ImportError as e:
        print(f"Import error: {e}")
        print("Failed to import required modules")
        sys.exit(1)