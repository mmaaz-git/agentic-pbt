#!/usr/bin/env python3
"""Run the pyramid.csrf property tests directly."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

# Import and run the tests
from test_pyramid_csrf import *
from hypothesis import settings

# Run each test
tests = [
    (test_simple_serializer_round_trip, "SimpleSerializer round-trip"),
    (test_strings_differ_correctness, "strings_differ correctness"),
    (test_strings_differ_same_string, "strings_differ same string"),
    (test_is_same_domain_exact_match, "is_same_domain exact match"),
    (test_is_same_domain_wildcard, "is_same_domain wildcard"),
    (test_is_same_domain_empty_pattern, "is_same_domain empty pattern"),
    (test_session_csrf_policy_token_consistency, "SessionCSRFStoragePolicy consistency"),
    (test_token_generation_uniqueness, "Token uniqueness"),
    (test_session_csrf_token_validation, "Session token validation"),
    (test_cookie_csrf_policy_initialization, "CookieCSRFStoragePolicy init"),
    (test_check_csrf_origin_same_origin, "check_csrf_origin same origin"),
    (test_is_same_domain_edge_cases, "is_same_domain edge cases"),
    (test_multiple_storage_policies_unique_tokens, "Multiple policies unique tokens"),
    (test_token_factory_format, "Token factory format"),
]

print("Running property-based tests for pyramid.csrf...")
print("=" * 60)

failed_tests = []
passed_tests = []

for test_func, test_name in tests:
    print(f"\nTesting: {test_name}")
    try:
        if test_func.__name__.startswith('test_') and hasattr(test_func, 'hypothesis'):
            # Hypothesis test - run with limited examples for speed
            with settings(max_examples=100):
                test_func()
        else:
            # Regular test
            test_func()
        print(f"  ✓ PASSED")
        passed_tests.append(test_name)
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        failed_tests.append((test_name, str(e)))

print("\n" + "=" * 60)
print(f"Results: {len(passed_tests)} passed, {len(failed_tests)} failed")

if failed_tests:
    print("\nFailed tests:")
    for name, error in failed_tests:
        print(f"  - {name}: {error}")
else:
    print("\nAll tests passed!")