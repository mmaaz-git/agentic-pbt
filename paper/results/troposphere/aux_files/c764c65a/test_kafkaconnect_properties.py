#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import pytest
import troposphere.kafkaconnect as kc
from troposphere.validators import integer, boolean

# Strategy for values that the integer validator accepts
@composite
def integer_validator_inputs(draw):
    """Generate values that the integer validator should accept"""
    choice = draw(st.integers(0, 5))
    if choice == 0:
        # Regular integers
        return draw(st.integers())
    elif choice == 1:
        # Strings that can be converted to int
        num = draw(st.integers(-10000, 10000))
        return str(num)
    elif choice == 2:
        # Bytes that can be converted to int
        num = draw(st.integers(0, 999))
        return str(num).encode()
    elif choice == 3:
        # Booleans (which are int subclass)
        return draw(st.booleans())
    elif choice == 4:
        # Floats with no fractional part
        num = draw(st.integers(-10000, 10000))
        return float(num)
    else:
        # Floats that happen to be whole numbers
        num = draw(st.integers(-10000, 10000))
        return num + 0.0

# Test 1: Integer validator type preservation bug
@given(integer_validator_inputs())
def test_integer_validator_type_preservation(value):
    """The integer validator should either convert to int or reject the value,
    but it actually preserves the original type"""
    
    # The validator accepts this value
    result = integer(value)
    
    # Property: If the validator accepts a value, it should return an integer
    # But this is NOT what happens - it returns the original value unchanged
    # This is a bug because the validator's name implies it produces integers
    
    # The actual behavior (which we'll test to confirm the bug)
    assert result == value  # Returns original value
    assert type(result) == type(value)  # Preserves original type
    
    # What we would expect from an "integer" validator:
    # assert isinstance(result, int)  # This would fail!

# Test 2: Round-trip serialization with type preservation issue
@given(integer_validator_inputs())
def test_round_trip_with_non_integer_types(value):
    """Round-trip serialization should preserve the value, 
    but non-integer types passing through the integer validator cause issues"""
    
    # Create an object with the value
    scale_in = kc.ScaleInPolicy(CpuUtilizationPercentage=value)
    
    # Serialize to dict
    dict_repr = scale_in.to_dict()
    
    # The value in the dict has the original type, not int
    stored_value = dict_repr['CpuUtilizationPercentage']
    assert type(stored_value) == type(value)
    
    # Round-trip: create from dict
    recreated = kc.ScaleInPolicy.from_dict("test", dict_repr)
    new_dict = recreated.to_dict()
    
    # The round-trip preserves the non-integer type
    assert new_dict['CpuUtilizationPercentage'] == value
    assert type(new_dict['CpuUtilizationPercentage']) == type(value)

# Test 3: AutoScaling with inconsistent worker counts
@given(
    max_workers=st.integers(1, 1000),
    min_workers=st.integers(1, 1000),
    mcu_count=st.integers(1, 100),
    scale_in_cpu=st.integers(1, 100),
    scale_out_cpu=st.integers(1, 100)
)
def test_autoscaling_worker_count_validation(max_workers, min_workers, mcu_count, 
                                              scale_in_cpu, scale_out_cpu):
    """AutoScaling should validate that min_workers <= max_workers, but it doesn't"""
    
    # Create AutoScaling with potentially invalid configuration
    auto = kc.AutoScaling(
        MaxWorkerCount=max_workers,
        MinWorkerCount=min_workers,
        McuCount=mcu_count,
        ScaleInPolicy=kc.ScaleInPolicy(CpuUtilizationPercentage=scale_in_cpu),
        ScaleOutPolicy=kc.ScaleOutPolicy(CpuUtilizationPercentage=scale_out_cpu)
    )
    
    # It accepts any configuration without validation
    dict_repr = auto.to_dict()
    assert dict_repr['MaxWorkerCount'] == max_workers
    assert dict_repr['MinWorkerCount'] == min_workers
    
    # Property that should hold but isn't enforced:
    # MinWorkerCount should be <= MaxWorkerCount
    # But the library doesn't validate this constraint

# Test 4: Required field validation with None values
@given(st.none() | st.integers())
def test_required_field_none_handling(value):
    """Required fields should reject None, but the behavior is inconsistent"""
    
    if value is None:
        # Should raise an error for required field with None
        with pytest.raises(Exception) as exc_info:
            kc.ScaleInPolicy(CpuUtilizationPercentage=None)
        assert "not a valid integer" in str(exc_info.value)
    else:
        # Should work with valid integer
        policy = kc.ScaleInPolicy(CpuUtilizationPercentage=value)
        assert policy.to_dict()['CpuUtilizationPercentage'] == value

# Test 5: Capacity mutual exclusivity not enforced
@given(
    auto_max=st.integers(1, 100),
    auto_min=st.integers(1, 100),
    auto_mcu=st.integers(1, 10),
    prov_workers=st.integers(1, 100),
    prov_mcu=st.integers(1, 10)
)
def test_capacity_mutual_exclusivity(auto_max, auto_min, auto_mcu, prov_workers, prov_mcu):
    """Capacity should enforce mutual exclusivity between AutoScaling and ProvisionedCapacity,
    but it accepts both simultaneously"""
    
    # Create both autoscaling and provisioned capacity
    auto = kc.AutoScaling(
        MaxWorkerCount=auto_max,
        MinWorkerCount=auto_min,
        McuCount=auto_mcu,
        ScaleInPolicy=kc.ScaleInPolicy(CpuUtilizationPercentage=20),
        ScaleOutPolicy=kc.ScaleOutPolicy(CpuUtilizationPercentage=80)
    )
    
    prov = kc.ProvisionedCapacity(
        WorkerCount=prov_workers,
        McuCount=prov_mcu
    )
    
    # The Capacity class accepts both, which shouldn't be valid
    # AWS CloudFormation would reject this, but the library doesn't validate it
    capacity = kc.Capacity(
        AutoScaling=auto,
        ProvisionedCapacity=prov
    )
    
    dict_repr = capacity.to_dict()
    assert 'AutoScaling' in dict_repr
    assert 'ProvisionedCapacity' in dict_repr
    # This creates invalid CloudFormation template

# Test 6: Boolean validator accepts unexpected string values
@given(st.text())
def test_boolean_validator_string_handling(text):
    """Boolean validator has specific string handling that might be unexpected"""
    
    # The boolean validator accepts specific strings
    if text in ["1", "true", "True"]:
        assert boolean(text) is True
    elif text in ["0", "false", "False"]:
        assert boolean(text) is False
    else:
        with pytest.raises(ValueError):
            boolean(text)

# Test 7: Type confusion with boolean/integer validators
@given(st.booleans())
def test_boolean_integer_confusion(value):
    """Booleans pass through integer validator unchanged, causing type confusion"""
    
    # Boolean passes integer validator
    result = integer(value)
    assert result == value
    assert type(result) is bool
    
    # This means CpuUtilizationPercentage can be a boolean
    policy = kc.ScaleInPolicy(CpuUtilizationPercentage=value)
    dict_repr = policy.to_dict()
    
    # The field that should be an integer percentage is now a boolean
    assert dict_repr['CpuUtilizationPercentage'] is value
    assert type(dict_repr['CpuUtilizationPercentage']) is bool
    
    # This could cause issues when the CloudFormation template is processed
    # as it expects an integer for CPU percentage, not a boolean

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])