#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Run each test individually to see which ones pass/fail
from test_docdb_properties import *

print("Running test_boolean_validator_valid_inputs...")
try:
    test_boolean_validator_valid_inputs()
    print("✓ PASSED")
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\nRunning test_integer_validator_valid_inputs...")
try:
    test_integer_validator_valid_inputs()
    print("✓ PASSED")
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\nRunning test_double_validator_valid_inputs...")
try:
    test_double_validator_valid_inputs()
    print("✓ PASSED")
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\nRunning test_valid_alphanumeric_titles...")
try:
    test_valid_alphanumeric_titles()
    print("✓ PASSED")
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\nRunning test_title_validation_rejects_non_alphanumeric...")
try:
    test_title_validation_rejects_non_alphanumeric()
    print("✓ PASSED")
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\nRunning test_dbcluster_to_dict_from_dict_roundtrip...")
try:
    test_dbcluster_to_dict_from_dict_roundtrip()
    print("✓ PASSED")
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nRunning test_serverless_scaling_configuration...")
try:
    test_serverless_scaling_configuration()
    print("✓ PASSED")
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\nRunning test_dbcluster_parameter_group_required_properties...")
try:
    test_dbcluster_parameter_group_required_properties()
    print("✓ PASSED")
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\nRunning test_dbinstance_required_properties...")
try:
    test_dbinstance_required_properties()
    print("✓ PASSED")
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\nRunning test_boolean_validator_invalid_inputs...")
try:
    test_boolean_validator_invalid_inputs()
    print("✓ PASSED")
except Exception as e:
    print(f"✗ FAILED: {e}")