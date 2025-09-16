#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from test_inquirerpy_properties import *
from hypothesis import settings

# Run each test with explicit settings
test_functions = [
    test_number_validator_integer_only,
    test_number_validator_float_allowed,
    test_empty_input_validator,
    test_password_validator_regex_construction,
    test_separator_string_representation,
    test_get_questions_dict_to_list,
    test_get_questions_list_passthrough,
    test_password_validator_acceptance,
    test_number_validator_special_floats
]

print("Running property-based tests for InquirerPy...")
print("=" * 60)

for test_func in test_functions:
    test_name = test_func.__name__
    print(f"\nTesting: {test_name}")
    print("-" * 40)
    
    try:
        # Run with limited examples to test quickly
        with settings(max_examples=100):
            test_func()
        print(f"✓ {test_name} passed")
    except AssertionError as e:
        print(f"✗ {test_name} FAILED")
        print(f"  Error: {e}")
    except Exception as e:
        print(f"✗ {test_name} ERROR")
        print(f"  Exception: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("Test run complete.")