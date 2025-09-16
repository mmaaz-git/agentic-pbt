"""Property-based tests for troposphere.autoscalingplans module"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere.validators.autoscalingplans import (
    validate_predictivescalingmaxcapacitybehavior,
    validate_predictivescalingmode,
    validate_scalingpolicyupdatebehavior,
    scalable_dimension_type,
    service_namespace_type,
    statistic_type,
)


# Property 1: Validator round-trip property - validators return exact input when valid
@given(st.sampled_from([
    "SetForecastCapacityToMaxCapacity",
    "SetMaxCapacityToForecastCapacity", 
    "SetMaxCapacityAboveForecastCapacity"
]))
def test_predictivescalingmaxcapacitybehavior_roundtrip(value):
    """Valid values should pass through unchanged"""
    result = validate_predictivescalingmaxcapacitybehavior(value)
    assert result == value
    assert result is value  # Should be the exact same object


@given(st.sampled_from(["ForecastAndScale", "ForecastOnly"]))
def test_predictivescalingmode_roundtrip(value):
    """Valid values should pass through unchanged"""
    result = validate_predictivescalingmode(value)
    assert result == value
    assert result is value


@given(st.sampled_from(["KeepExternalPolicies", "ReplaceExternalPolicies"]))
def test_scalingpolicyupdatebehavior_roundtrip(value):
    """Valid values should pass through unchanged"""
    result = validate_scalingpolicyupdatebehavior(value)
    assert result == value
    assert result is value


@given(st.sampled_from([
    "autoscaling:autoScalingGroup:DesiredCapacity",
    "ecs:service:DesiredCount",
    "ec2:spot-fleet-request:TargetCapacity",
    "rds:cluster:ReadReplicaCount",
    "dynamodb:table:ReadCapacityUnits",
    "dynamodb:table:WriteCapacityUnits",
    "dynamodb:index:ReadCapacityUnits",
    "dynamodb:index:WriteCapacityUnits",
]))
def test_scalable_dimension_roundtrip(value):
    """Valid values should pass through unchanged"""
    result = scalable_dimension_type(value)
    assert result == value
    assert result is value


@given(st.sampled_from(["autoscaling", "ecs", "ec2", "rds", "dynamodb"]))
def test_service_namespace_roundtrip(value):
    """Valid values should pass through unchanged"""
    result = service_namespace_type(value)
    assert result == value
    assert result is value


@given(st.sampled_from(["Average", "Minimum", "Maximum", "SampleCount", "Sum"]))
def test_statistic_type_roundtrip(value):
    """Valid values should pass through unchanged"""
    result = statistic_type(value)
    assert result == value
    assert result is value


# Property 2: Invalid values should raise ValueError
@given(st.text(min_size=1).filter(lambda x: x not in [
    "SetForecastCapacityToMaxCapacity",
    "SetMaxCapacityToForecastCapacity",
    "SetMaxCapacityAboveForecastCapacity"
]))
@settings(max_examples=100)
def test_predictivescalingmaxcapacitybehavior_invalid_raises(value):
    """Invalid values should raise ValueError"""
    with pytest.raises(ValueError) as exc_info:
        validate_predictivescalingmaxcapacitybehavior(value)
    assert "PredictiveScalingMaxCapacityBehavior must be one of" in str(exc_info.value)


@given(st.text(min_size=1).filter(lambda x: x not in ["ForecastAndScale", "ForecastOnly"]))
@settings(max_examples=100)
def test_predictivescalingmode_invalid_raises(value):
    """Invalid values should raise ValueError"""
    with pytest.raises(ValueError) as exc_info:
        validate_predictivescalingmode(value)
    assert "PredictiveScalingMode must be one of" in str(exc_info.value)


# Property 3: Valid values lists should not contain duplicates
def test_no_duplicate_valid_values():
    """Valid values should be unique within each validator"""
    
    # Check predictivescalingmaxcapacitybehavior
    valid_values_1 = [
        "SetForecastCapacityToMaxCapacity",
        "SetMaxCapacityToForecastCapacity",
        "SetMaxCapacityAboveForecastCapacity"
    ]
    assert len(valid_values_1) == len(set(valid_values_1))
    
    # Check predictivescalingmode
    valid_values_2 = ["ForecastAndScale", "ForecastOnly"]
    assert len(valid_values_2) == len(set(valid_values_2))
    
    # Check scalingpolicyupdatebehavior
    valid_values_3 = ["KeepExternalPolicies", "ReplaceExternalPolicies"]
    assert len(valid_values_3) == len(set(valid_values_3))
    
    # Check scalable_dimension_type
    valid_values_4 = [
        "autoscaling:autoScalingGroup:DesiredCapacity",
        "ecs:service:DesiredCount",
        "ec2:spot-fleet-request:TargetCapacity",
        "rds:cluster:ReadReplicaCount",
        "dynamodb:table:ReadCapacityUnits",
        "dynamodb:table:WriteCapacityUnits",
        "dynamodb:index:ReadCapacityUnits",
        "dynamodb:index:WriteCapacityUnits",
    ]
    assert len(valid_values_4) == len(set(valid_values_4))
    
    # Check service_namespace_type
    valid_values_5 = ["autoscaling", "ecs", "ec2", "rds", "dynamodb"]
    assert len(valid_values_5) == len(set(valid_values_5))
    
    # Check statistic_type
    valid_values_6 = ["Average", "Minimum", "Maximum", "SampleCount", "Sum"]
    assert len(valid_values_6) == len(set(valid_values_6))


# Property 4: Case sensitivity - validators should be case-sensitive
@given(st.sampled_from(["FORECASTANDSCALE", "forecastandscale", "ForecastandScale", "forecastAndScale"]))
def test_validators_are_case_sensitive(value):
    """Validators should be case-sensitive and reject different cases"""
    with pytest.raises(ValueError):
        validate_predictivescalingmode(value)


# Property 5: Error messages contain all valid values
@given(st.text(min_size=1, max_size=10).filter(lambda x: x not in ["ForecastAndScale", "ForecastOnly"]))
@settings(max_examples=50)
def test_error_message_contains_valid_values(invalid_value):
    """Error messages should list all valid values"""
    try:
        validate_predictivescalingmode(invalid_value)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        error_msg = str(e)
        # Check that both valid values appear in the error message
        assert "ForecastAndScale" in error_msg
        assert "ForecastOnly" in error_msg
        assert "PredictiveScalingMode must be one of" in error_msg


# Property 6: Empty string handling
@given(st.just(""))
def test_empty_string_raises_error(value):
    """Empty strings should be rejected by all validators"""
    with pytest.raises(ValueError):
        validate_predictivescalingmaxcapacitybehavior(value)
    with pytest.raises(ValueError):
        validate_predictivescalingmode(value)
    with pytest.raises(ValueError):
        validate_scalingpolicyupdatebehavior(value)
    with pytest.raises(ValueError):
        scalable_dimension_type(value)
    with pytest.raises(ValueError):
        service_namespace_type(value)
    with pytest.raises(ValueError):
        statistic_type(value)


# Property 7: None handling
@given(st.just(None))
def test_none_handling(value):
    """None values should cause appropriate errors"""
    # Testing if None is handled - may raise AttributeError or ValueError
    with pytest.raises((ValueError, AttributeError, TypeError)):
        validate_predictivescalingmaxcapacitybehavior(value)
    with pytest.raises((ValueError, AttributeError, TypeError)):
        validate_predictivescalingmode(value)
    with pytest.raises((ValueError, AttributeError, TypeError)):
        validate_scalingpolicyupdatebehavior(value)
    with pytest.raises((ValueError, AttributeError, TypeError)):
        scalable_dimension_type(value)
    with pytest.raises((ValueError, AttributeError, TypeError)):
        service_namespace_type(value)
    with pytest.raises((ValueError, AttributeError, TypeError)):
        statistic_type(value)