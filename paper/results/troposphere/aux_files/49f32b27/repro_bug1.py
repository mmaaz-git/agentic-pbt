"""Reproduce Bug 1: EXACT_CAPACITY accepts 0 but should be positive"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import emr
from troposphere.validators import emr as emr_validators

# Test: EXACT_CAPACITY should require positive integer
config = emr.SimpleScalingPolicyConfiguration(
    AdjustmentType=emr_validators.EXACT_CAPACITY,
    ScalingAdjustment=0
)

try:
    config.validate()
    print("VALIDATION PASSED: ScalingAdjustment=0 with EXACT_CAPACITY was accepted")
    print("This is a BUG: EXACT_CAPACITY should require positive integer > 0")
except ValueError as e:
    print(f"VALIDATION FAILED (expected): {e}")

# Test with negative value
config2 = emr.SimpleScalingPolicyConfiguration(
    AdjustmentType=emr_validators.EXACT_CAPACITY,
    ScalingAdjustment=-1
)

try:
    config2.validate()
    print("VALIDATION PASSED: ScalingAdjustment=-1 with EXACT_CAPACITY was accepted")
    print("This is a BUG")
except ValueError as e:
    print(f"VALIDATION FAILED for -1 (expected): {e}")