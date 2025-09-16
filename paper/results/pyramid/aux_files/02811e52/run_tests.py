#!/usr/bin/env python3
"""Simple test runner for pyramid.viewderivers tests."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import test_viewderivers

# Run each test function
test_functions = [
    test_viewderivers.test_preserve_view_attrs_none_view,
    test_viewderivers.test_preserve_view_attrs_same_view_wrapper,
    test_viewderivers.test_preserve_view_attrs_copies_attributes,
    test_viewderivers.test_preserve_view_attrs_handles_missing_name,
    test_viewderivers.test_view_description_with_text_attr,
    test_viewderivers.test_view_description_without_text_attr,
    test_viewderivers.test_default_view_mapper_unbound_method_error,
    test_viewderivers.test_default_view_mapper_class_sets_text,
    test_viewderivers.test_http_cached_view_invalid_tuple,
    test_viewderivers.test_http_cached_view_with_integer,
    test_viewderivers.test_http_cached_view_with_tuple,
    test_viewderivers.test_requestonly_with_single_arg_function,
    test_viewderivers.test_requestonly_with_multiple_args,
    test_viewderivers.test_requestonly_with_class,
]

print("Running property-based tests for pyramid.viewderivers...")
failures = []

for test_func in test_functions:
    try:
        print(f"Running {test_func.__name__}...", end=" ")
        test_func()
        print("✓")
    except Exception as e:
        print(f"✗ FAILED")
        failures.append((test_func.__name__, e))

if failures:
    print(f"\n{len(failures)} tests failed:")
    for name, error in failures:
        print(f"  - {name}: {error}")
    sys.exit(1)
else:
    print(f"\nAll {len(test_functions)} tests passed!")
    sys.exit(0)