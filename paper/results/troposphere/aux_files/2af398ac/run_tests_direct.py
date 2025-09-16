#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import test_troposphere_budgets
from hypothesis import settings
import traceback

test_functions = [
    test_troposphere_budgets.test_boolean_validator_valid_inputs,
    test_troposphere_budgets.test_boolean_validator_invalid_inputs,
    test_troposphere_budgets.test_integer_validator_valid_inputs,
    test_troposphere_budgets.test_double_validator_valid_inputs,
    test_troposphere_budgets.test_cost_types_boolean_properties,
    test_troposphere_budgets.test_spend_object_creation,
    test_troposphere_budgets.test_notification_creation_and_round_trip,
    test_troposphere_budgets.test_subscriber_creation,
    test_troposphere_budgets.test_resource_tag_creation,
    test_troposphere_budgets.test_historical_options_integer_validation,
    test_troposphere_budgets.test_scp_action_definition,
    test_troposphere_budgets.test_ssm_action_definition,
    test_troposphere_budgets.test_action_threshold_double_validation,
]

failures = []
for test_func in test_functions:
    print(f"\nRunning {test_func.__name__}...", end=" ")
    try:
        test_func()
        print("PASSED")
    except Exception as e:
        print(f"FAILED")
        print(f"  Error: {e}")
        traceback.print_exc()
        failures.append((test_func.__name__, e))

print(f"\n\n{'='*60}")
print(f"Test Summary: {len(test_functions) - len(failures)}/{len(test_functions)} passed")
if failures:
    print("\nFailed tests:")
    for name, error in failures:
        print(f"  - {name}: {error}")