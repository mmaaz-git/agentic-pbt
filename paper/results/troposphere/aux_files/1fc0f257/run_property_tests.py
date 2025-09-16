#!/usr/bin/env python3
"""Run property-based tests for troposphere.iotthingsgraph"""

import sys
import traceback

# Add the troposphere environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import the test module
import test_iotthingsgraph_properties as test_module

# Get all test functions
test_functions = [
    getattr(test_module, name)
    for name in dir(test_module)
    if name.startswith("test_")
]

print(f"Found {len(test_functions)} test functions")
print("=" * 60)

failures = []

for test_func in test_functions:
    test_name = test_func.__name__
    print(f"\nRunning: {test_name}")
    print("-" * 40)
    
    try:
        # Run the test
        test_func()
        print(f"✓ {test_name} PASSED")
    except Exception as e:
        print(f"✗ {test_name} FAILED")
        print(f"Error: {e}")
        traceback.print_exc()
        failures.append((test_name, e))

print("\n" + "=" * 60)
print(f"SUMMARY: {len(test_functions) - len(failures)}/{len(test_functions)} tests passed")

if failures:
    print("\nFailed tests:")
    for name, error in failures:
        print(f"  - {name}: {error}")
    sys.exit(1)