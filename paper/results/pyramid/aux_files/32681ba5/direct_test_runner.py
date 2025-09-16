#!/usr/bin/env python3
import sys
import os
import traceback
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
from hypothesis.errors import FailedHealthCheck

# Import our test module
import test_trino_auth_properties as test_module

# Get all test functions
test_functions = [
    (name, getattr(test_module, name)) 
    for name in dir(test_module) 
    if name.startswith('test_') and callable(getattr(test_module, name))
]

print(f"Found {len(test_functions)} test functions")
print("=" * 60)

failed_tests = []
passed_tests = []

for test_name, test_func in test_functions:
    print(f"\nRunning {test_name}...")
    try:
        # Run the test with reduced examples for speed
        with settings(max_examples=10, deadline=None):
            test_func()
        print(f"✓ {test_name} PASSED")
        passed_tests.append(test_name)
    except Exception as e:
        print(f"✗ {test_name} FAILED")
        print(f"  Error: {str(e)}")
        print(f"  Traceback:")
        traceback.print_exc()
        failed_tests.append((test_name, e))
        
print("\n" + "=" * 60)
print(f"SUMMARY: {len(passed_tests)} passed, {len(failed_tests)} failed")

if failed_tests:
    print("\nFailed tests:")
    for test_name, error in failed_tests:
        print(f"  - {test_name}: {str(error)[:100]}...")
        
sys.exit(0 if not failed_tests else 1)