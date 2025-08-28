#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python
"""Simple test runner that executes our tests"""

import sys
import traceback
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import test file
from test_troposphere_macie import *

# Run each test function manually
test_functions = [
    test_findingsfilter_action_valid,
    test_findingsfilter_action_invalid,
    test_session_findingpublishingfrequency_valid,
    test_session_findingpublishingfrequency_invalid,
    test_session_status_valid,
    test_session_status_invalid,
    test_s3wordslist_creation,
    test_customdataidentifier_creation,
    test_criterionadditionalproperties_integer_fields,
    test_criterionadditionalproperties_list_fields,
    test_session_with_validators,
    test_s3wordslist_type_validation,
    test_allowlist_requires_criteria,
    test_customdataidentifier_list_properties,
    test_customdataidentifier_integer_validation
]

print("Running property-based tests for troposphere.macie...")
print("-" * 60)

passed = 0
failed = 0
errors = []

for test_func in test_functions:
    test_name = test_func.__name__
    try:
        # Run the test (hypothesis will run it multiple times)
        test_func()
        print(f"✓ {test_name}")
        passed += 1
    except Exception as e:
        print(f"✗ {test_name}")
        print(f"  Error: {e}")
        failed += 1
        errors.append((test_name, e, traceback.format_exc()))

print("-" * 60)
print(f"Results: {passed} passed, {failed} failed")

if errors:
    print("\n" + "=" * 60)
    print("DETAILED ERROR INFORMATION:")
    print("=" * 60)
    for test_name, error, tb in errors:
        print(f"\nTest: {test_name}")
        print(f"Error: {error}")
        print("Traceback:")
        print(tb)