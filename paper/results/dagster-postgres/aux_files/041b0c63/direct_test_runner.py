#!/usr/bin/env python3
import sys
import os

# Add the site-packages directory to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

# Import the test module
import test_dagster_postgres_properties

# Run each test method manually
from hypothesis import given, strategies as st, settings
import traceback

test_classes = [
    test_dagster_postgres_properties.TestGetConnString,
    test_dagster_postgres_properties.TestPgUrlFromConfig,
    test_dagster_postgres_properties.TestRetryFunctions,
]

print("Running property-based tests for dagster_postgres...")
print("=" * 60)

failed_tests = []
passed_tests = []

for test_class in test_classes:
    test_instance = test_class()
    test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
    
    print(f"\nTesting {test_class.__name__}:")
    print("-" * 40)
    
    for method_name in test_methods:
        method = getattr(test_instance, method_name)
        test_name = f"{test_class.__name__}.{method_name}"
        
        try:
            print(f"  Running {method_name}...", end=" ")
            method()
            print("✓ PASSED")
            passed_tests.append(test_name)
        except Exception as e:
            print(f"✗ FAILED")
            print(f"    Error: {e}")
            print(f"    Traceback:")
            traceback.print_exc()
            failed_tests.append((test_name, e))

print("\n" + "=" * 60)
print(f"Test Summary: {len(passed_tests)} passed, {len(failed_tests)} failed")

if failed_tests:
    print("\nFailed tests:")
    for test_name, error in failed_tests:
        print(f"  - {test_name}: {str(error)[:100]}...")
        
sys.exit(0 if not failed_tests else 1)