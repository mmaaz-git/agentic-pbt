#!/usr/bin/env python3
"""Run all Fire property-based tests and report findings."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 70)
    print("PYTHON FIRE PROPERTY-BASED TESTING SUITE")
    print("=" * 70)
    print()
    
    all_passed = True
    
    # Run basic property tests
    print("1. RUNNING BASIC PROPERTY TESTS")
    print("-" * 70)
    try:
        import run_fire_tests
        run_fire_tests.main()
    except Exception as e:
        print(f"Error running basic tests: {e}")
        all_passed = False
    
    print("\n")
    
    # Run edge case tests
    print("2. RUNNING EDGE CASE TESTS")
    print("-" * 70)
    try:
        import test_fire_edge_cases
        test_fire_edge_cases.run_edge_case_tests()
    except Exception as e:
        print(f"Error running edge case tests: {e}")
        all_passed = False
    
    print("\n")
    
    # Run bug hunting tests
    print("3. RUNNING BUG HUNTING TESTS")
    print("-" * 70)
    try:
        import test_fire_bugs
        bugs = test_fire_bugs.run_bug_hunt()
        if bugs:
            all_passed = False
    except Exception as e:
        print(f"Error running bug hunt tests: {e}")
        all_passed = False
    
    print("\n")
    print("=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)
    
    if all_passed:
        print("\n✅ All property-based tests passed successfully!")
        print("No bugs found in the Python Fire library.")
    else:
        print("\n⚠️ Some tests failed or revealed potential issues.")
        print("Review the output above for details.")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())