#!/usr/bin/env python3
"""Run the property-based tests for trino.client."""

import sys
import traceback

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

# Import the test module
import test_trino_client_properties as test_module

# Get all test functions
test_functions = [
    getattr(test_module, name) for name in dir(test_module) 
    if name.startswith('test_') and callable(getattr(test_module, name))
]

print(f"Found {len(test_functions)} test functions")
print("=" * 60)

failed_tests = []

for test_func in test_functions:
    test_name = test_func.__name__
    print(f"\nRunning {test_name}...")
    
    try:
        # Run the test
        test_func()
        print(f"✓ {test_name} passed")
    except Exception as e:
        print(f"✗ {test_name} FAILED")
        print(f"  Error: {e}")
        traceback.print_exc()
        failed_tests.append((test_name, e))

print("\n" + "=" * 60)
print(f"\nSummary: {len(test_functions) - len(failed_tests)}/{len(test_functions)} tests passed")

if failed_tests:
    print("\nFailed tests:")
    for name, error in failed_tests:
        print(f"  - {name}: {error}")
    sys.exit(1)