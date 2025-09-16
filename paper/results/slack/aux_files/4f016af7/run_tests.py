#!/usr/bin/env python3
import sys
sys.path.append('/root/hypothesis-llm/envs/slack_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import traceback

import test_slack_properties

test_functions = [
    test_slack_properties.test_container_registration_and_retrieval,
    test_slack_properties.test_container_group_registration,
    test_slack_properties.test_container_idempotent_provide,
    test_slack_properties.test_container_reset_group,
    test_slack_properties.test_unregistered_component_raises_exception,
    test_slack_properties.test_unregistered_attribute_access_raises,
    test_slack_properties.test_invoke_with_matching_params,
    test_slack_properties.test_invoke_missing_required_param_raises,
    test_slack_properties.test_invoke_with_defaults,
    test_slack_properties.test_container_accessed_property,
    test_slack_properties.test_container_delattr,
    test_slack_properties.test_container_multiple_registrations,
    test_slack_properties.test_container_callable_registration,
    test_slack_properties.test_container_init_with_kwargs,
    test_slack_properties.test_container_init_with_protos,
    test_slack_properties.test_invoke_with_class_constructor,
    test_slack_properties.test_invoke_parameter_priority,
    test_slack_properties.test_container_inject_method,
    test_slack_properties.test_container_apply_method,
]

failures = []

for test_func in test_functions:
    print(f"Running {test_func.__name__}...")
    try:
        test_func()
        print(f"  ✓ PASSED")
    except Exception as e:
        print(f"  ✗ FAILED")
        print(f"    Error: {e}")
        traceback.print_exc()
        failures.append((test_func.__name__, e))
        print()

print("\n" + "="*60)
if failures:
    print(f"FAILURES: {len(failures)} out of {len(test_functions)} tests failed")
    for name, error in failures:
        print(f"  - {name}: {error}")
else:
    print(f"SUCCESS: All {len(test_functions)} tests passed!")