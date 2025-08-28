#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.strategies import composite
import pytest
import troposphere.kafkaconnect as kc
from troposphere.validators import integer, boolean

# Bug 1: Integer validator doesn't validate integer range for CPU percentages
@given(st.integers())
@example(-1)  # Negative CPU percentage
@example(101)  # > 100% CPU
@example(1000000)  # Absurdly high
def test_cpu_percentage_accepts_invalid_ranges(value):
    """CPU utilization percentage should be 0-100, but accepts any integer"""
    
    # This should ideally validate that CPU percentage is between 0-100
    # But it accepts any integer value
    policy = kc.ScaleInPolicy(CpuUtilizationPercentage=value)
    dict_repr = policy.to_dict()
    
    # The value is accepted even if it's nonsensical for CPU percentage
    assert dict_repr['CpuUtilizationPercentage'] == value
    
    # Document the bug: CPU percentage of -1 or 1000000 doesn't make sense
    if value < 0 or value > 100:
        # This should have raised a validation error but didn't
        # AWS CloudFormation will reject this, but troposphere doesn't validate it
        pass

# Bug 2: Type confusion allows booleans as CPU percentages
@given(st.booleans())
def test_boolean_as_cpu_percentage_bug(value):
    """CpuUtilizationPercentage accepts boolean values, which is nonsensical"""
    
    # A boolean (True/False) as CPU percentage doesn't make sense
    policy = kc.ScaleInPolicy(CpuUtilizationPercentage=value)
    dict_repr = policy.to_dict()
    
    # Bug: The field accepts True/False as CPU utilization percentage
    assert dict_repr['CpuUtilizationPercentage'] is value
    
    # This will generate invalid CloudFormation:
    # CpuUtilizationPercentage: true  (instead of a number 0-100)

# Bug 3: String integers pass validation but create invalid CloudFormation
@given(st.integers(0, 100))
def test_string_integer_creates_invalid_cloudformation(int_value):
    """String representations of integers create invalid CloudFormation JSON"""
    
    # Pass a string instead of integer
    str_value = str(int_value)
    policy = kc.ScaleInPolicy(CpuUtilizationPercentage=str_value)
    
    # The value is stored as a string
    dict_repr = policy.to_dict()
    assert dict_repr['CpuUtilizationPercentage'] == str_value
    assert isinstance(dict_repr['CpuUtilizationPercentage'], str)
    
    # When serialized to JSON for CloudFormation, this creates:
    # "CpuUtilizationPercentage": "50"  (string)
    # Instead of:
    # "CpuUtilizationPercentage": 50    (number)
    
    # CloudFormation expects a number, not a string
    json_output = json.dumps(dict_repr)
    assert f'"{str_value}"' in json_output  # String is quoted in JSON
    # This will fail CloudFormation validation

# Bug 4: Invalid MinWorkerCount > MaxWorkerCount accepted
@given(
    min_workers=st.integers(50, 100),
    max_workers=st.integers(1, 49)
)
def test_invalid_worker_count_relationship(min_workers, max_workers):
    """AutoScaling accepts MinWorkerCount > MaxWorkerCount, which is invalid"""
    
    assume(min_workers > max_workers)
    
    # This configuration is nonsensical: minimum > maximum
    auto = kc.AutoScaling(
        MaxWorkerCount=max_workers,
        MinWorkerCount=min_workers,
        McuCount=1,
        ScaleInPolicy=kc.ScaleInPolicy(CpuUtilizationPercentage=20),
        ScaleOutPolicy=kc.ScaleOutPolicy(CpuUtilizationPercentage=80)
    )
    
    dict_repr = auto.to_dict()
    
    # Bug: Accepts invalid configuration where min > max
    assert dict_repr['MinWorkerCount'] > dict_repr['MaxWorkerCount']
    # AWS will reject this configuration

# Bug 5: Bytes type creates invalid CloudFormation
@given(st.integers(0, 100))
def test_bytes_creates_invalid_cloudformation(value):
    """Bytes values pass validation but create unparseable CloudFormation"""
    
    bytes_value = str(value).encode('utf-8')
    
    # Bytes pass the integer validator
    policy = kc.ScaleInPolicy(CpuUtilizationPercentage=bytes_value)
    dict_repr = policy.to_dict()
    
    # The bytes object is stored
    assert dict_repr['CpuUtilizationPercentage'] == bytes_value
    assert isinstance(dict_repr['CpuUtilizationPercentage'], bytes)
    
    # Bytes objects can't be serialized to JSON
    with pytest.raises(TypeError) as exc_info:
        json.dumps(dict_repr)
    
    assert "not JSON serializable" in str(exc_info.value) or \
           "bytes" in str(exc_info.value).lower()

# Bug 6: Float values for integer fields
@given(st.floats(min_value=0.1, max_value=99.9).filter(lambda x: x != int(x)))
def test_float_with_decimals_as_integer(value):
    """Float values with decimals pass integer validation incorrectly"""
    
    # Ensure we have a float with decimal part
    assume(value != int(value))
    
    # This should fail validation but might not
    try:
        policy = kc.ScaleInPolicy(CpuUtilizationPercentage=value)
        dict_repr = policy.to_dict()
        
        # If it accepts the float, that's questionable for CPU percentage
        # which should be a whole number
        assert dict_repr['CpuUtilizationPercentage'] == value
        
        # AWS expects integer for CpuUtilizationPercentage
        # A float like 50.7 doesn't make sense for CPU percentage
    except ValueError:
        # This is the expected behavior - reject non-integer floats
        pass

# Bug 7: Empty string passes some validators
@given(st.just(""))
def test_empty_string_validation(value):
    """Empty strings might pass validation incorrectly"""
    
    # Empty string for integer field should fail
    with pytest.raises(ValueError) as exc_info:
        policy = kc.ScaleInPolicy(CpuUtilizationPercentage=value)
    
    assert "not a valid integer" in str(exc_info.value)

# Bug 8: Very large integers cause issues
@given(st.integers(min_value=10**100, max_value=10**200))
def test_extremely_large_integers(value):
    """Extremely large integers might cause issues in CloudFormation"""
    
    policy = kc.ScaleInPolicy(CpuUtilizationPercentage=value)
    dict_repr = policy.to_dict()
    
    # The value is accepted even though it's absurdly large for CPU percentage
    assert dict_repr['CpuUtilizationPercentage'] == value
    
    # This will likely cause issues in CloudFormation
    # CPU percentage should be 0-100, not 10^100

# Bug 9: Scale in/out policy relationship not validated
@given(
    scale_in=st.integers(0, 100),
    scale_out=st.integers(0, 100)
)
def test_scale_policy_relationship(scale_in, scale_out):
    """Scale-in threshold can be higher than scale-out threshold, which is illogical"""
    
    # If scale_in > scale_out, the policies conflict
    auto = kc.AutoScaling(
        MaxWorkerCount=10,
        MinWorkerCount=1,
        McuCount=1,
        ScaleInPolicy=kc.ScaleInPolicy(CpuUtilizationPercentage=scale_in),
        ScaleOutPolicy=kc.ScaleOutPolicy(CpuUtilizationPercentage=scale_out)
    )
    
    dict_repr = auto.to_dict()
    
    # Document when policies don't make sense
    if scale_in >= scale_out:
        # Bug: Scale-in at higher CPU than scale-out doesn't make sense
        # Should scale out when CPU is high, scale in when CPU is low
        # But this accepts scale-in at 80% and scale-out at 20%
        pass

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])