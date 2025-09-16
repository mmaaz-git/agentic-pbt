#!/usr/bin/env python3
"""Run the property-based tests manually."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import test_firehose_validators

# Run each test function
test_functions = [
    test_firehose_validators.test_processor_type_accepts_valid,
    test_firehose_validators.test_delivery_stream_type_accepts_valid,
    test_firehose_validators.test_index_rotation_accepts_valid,
    test_firehose_validators.test_s3_backup_mode_elastic_accepts_valid,
    test_firehose_validators.test_s3_backup_mode_extended_accepts_valid,
    test_firehose_validators.test_processor_type_rejects_invalid,
    test_firehose_validators.test_delivery_stream_type_rejects_invalid,
    test_firehose_validators.test_processor_type_idempotent,
    test_firehose_validators.test_delivery_stream_error_format,
    test_firehose_validators.test_processor_type_case_sensitive,
    test_firehose_validators.test_validators_handle_none,
    test_firehose_validators.test_validators_handle_empty_string,
    test_firehose_validators.test_s3_backup_validators_distinct,
]

print("Running property-based tests for troposphere.firehose validators...")
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