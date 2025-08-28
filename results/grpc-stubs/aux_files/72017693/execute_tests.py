#!/usr/bin/env python3
"""Direct test execution."""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

# Import test module
import test_grpc_status_properties as test_module
from hypothesis import given, strategies as st, settings

# Run each test with a limited number of examples for quick feedback
print("Running property-based tests for grpc_status module...\n")

tests = [
    ("test_code_to_grpc_status_code_bijection", test_module.test_code_to_grpc_status_code_bijection),
    ("test_from_call_validation", test_module.test_from_call_validation),
    ("test_to_status_creates_valid_status", test_module.test_to_status_creates_valid_status),
    ("test_to_status_round_trip", test_module.test_to_status_round_trip),
    ("test_from_call_none_metadata", test_module.test_from_call_none_metadata),
    ("test_from_call_missing_key", test_module.test_from_call_missing_key),
]

for test_name, test_func in tests:
    print(f"Running {test_name}...")
    try:
        # Apply settings to limit examples
        with settings(max_examples=100):
            test_func()
        print(f"  ✓ {test_name} passed\n")
    except Exception as e:
        print(f"  ✗ {test_name} failed: {e}\n")
        import traceback
        traceback.print_exc()
        print()

print("Test execution complete.")