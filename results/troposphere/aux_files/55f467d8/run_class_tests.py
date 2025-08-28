#!/usr/bin/env python3
"""Run the class-based property tests manually."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import test_firehose_classes

# Run each test function
test_functions = [
    test_firehose_classes.test_all_awsproperty_have_props,
    test_firehose_classes.test_required_props_consistency,
    test_firehose_classes.test_property_naming_conventions,
    test_firehose_classes.test_buffering_hints_accepts_integers,
    test_firehose_classes.test_s3_configuration_consistency,
    test_firehose_classes.test_delivery_stream_resource_type,
    test_firehose_classes.test_validator_imports,
    test_firehose_classes.test_integer_properties_accept_integers,
    test_firehose_classes.test_similar_classes_consistency,
    test_firehose_classes.test_retry_options_consistency,
    test_firehose_classes.test_s3_backup_mode_validator_usage,
]

print("Running property-based tests for troposphere.firehose classes...")
print("=" * 60)

failures = []
for test_func in test_functions:
    test_name = test_func.__name__
    print(f"\nRunning {test_name}...")
    try:
        test_func()
        print(f"  ✓ {test_name} passed")
    except Exception as e:
        print(f"  ✗ {test_name} failed: {e}")
        failures.append((test_name, e))

print("\n" + "=" * 60)
if failures:
    print(f"\n{len(failures)} test(s) failed:")
    for name, error in failures:
        print(f"  - {name}: {error}")
else:
    print("\nAll tests passed!")