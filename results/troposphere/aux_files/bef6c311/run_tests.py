#!/usr/bin/env python3
"""Simple test runner to execute our tests"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import our test module
import test_troposphere_ce

# Run each test function manually
test_functions = [
    test_troposphere_ce.test_resource_tag_roundtrip,
    test_troposphere_ce.test_resource_tag_missing_value_fails,
    test_troposphere_ce.test_resource_tag_missing_key_fails,
    test_troposphere_ce.test_anomaly_subscription_threshold_accepts_floats,
    test_troposphere_ce.test_double_validator_rejects_invalid_input,
    test_troposphere_ce.test_subscriber_creation,
    test_troposphere_ce.test_anomaly_monitor_creation,
    test_troposphere_ce.test_cost_category_creation,
    test_troposphere_ce.test_resource_tags_list_serialization,
    test_troposphere_ce.test_empty_string_validation,
    test_troposphere_ce.test_json_serialization_invariant,
]

for test_func in test_functions:
    print(f"\nRunning {test_func.__name__}...")
    try:
        test_func()
        print(f"  ✓ {test_func.__name__} passed")
    except Exception as e:
        print(f"  ✗ {test_func.__name__} failed: {e}")