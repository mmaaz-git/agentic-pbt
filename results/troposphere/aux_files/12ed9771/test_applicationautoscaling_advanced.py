#!/usr/bin/env python3
"""Advanced property-based tests for troposphere.applicationautoscaling module."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import pytest
import json

# Import the modules to test
from troposphere.validators import integer, double, boolean
from troposphere import applicationautoscaling as appscaling
from troposphere import Ref, Template


# Property: Test integer validator with edge cases
@given(st.one_of(
    st.floats(allow_nan=True, allow_infinity=True),
    st.text(),
    st.binary(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator_edge_cases(x):
    """Test integer validator with various edge case inputs."""
    try:
        result = integer(x)
        # If it succeeds, we should be able to convert to int
        int_val = int(result)
    except (ValueError, TypeError) as e:
        # This is expected for invalid inputs
        pass


# Property: Test double validator with special float values
@given(st.floats())
def test_double_validator_special_floats(x):
    """Test double validator with NaN and infinity."""
    try:
        result = double(x)
        # If it succeeds, input should be convertible to float
        float_val = float(result)
        assert result == x
    except (ValueError, TypeError):
        # Should fail for truly invalid inputs
        try:
            float(x)
            # If float() works but double() failed, that's potentially a bug
            if x != x:  # NaN check
                pass  # NaN might be rejected intentionally
            else:
                assert False, f"double() rejected valid float: {x}"
        except (ValueError, TypeError):
            pass


# Property: boolean validator with unexpected inputs
@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(),
    st.lists(st.booleans()),
    st.none()
))
def test_boolean_validator_unexpected_inputs(x):
    """Test boolean validator with various unexpected inputs."""
    try:
        result = boolean(x)
        # Check documented valid inputs
        assert x in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]
        assert isinstance(result, bool)
    except ValueError:
        # Should reject anything not in the valid list
        assert x not in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]


# Property: Complex nested structure serialization
@given(
    st.integers(min_value=1, max_value=1000),
    st.integers(min_value=1, max_value=1000),
    st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False)
)
def test_scaling_policy_complex_structure(min_cap, max_cap, target_value):
    """Test ScalingPolicy with nested configuration objects."""
    # Create a complex scaling policy with nested objects
    policy = appscaling.ScalingPolicy(
        "TestPolicy",
        PolicyName="test-policy",
        PolicyType="TargetTrackingScaling",
        TargetTrackingScalingPolicyConfiguration=appscaling.TargetTrackingScalingPolicyConfiguration(
            TargetValue=target_value,
            PredefinedMetricSpecification=appscaling.PredefinedMetricSpecification(
                PredefinedMetricType="DynamoDBReadCapacityUtilization"
            )
        )
    )
    
    # Convert to dict
    policy_dict = policy.to_dict()
    
    # Verify structure
    assert policy_dict["Type"] == "AWS::ApplicationAutoScaling::ScalingPolicy"
    assert policy_dict["Properties"]["PolicyName"] == "test-policy"
    assert policy_dict["Properties"]["PolicyType"] == "TargetTrackingScaling"
    
    # Check nested structure
    config = policy_dict["Properties"]["TargetTrackingScalingPolicyConfiguration"]
    assert config["TargetValue"] == target_value
    assert "PredefinedMetricSpecification" in config
    assert config["PredefinedMetricSpecification"]["PredefinedMetricType"] == "DynamoDBReadCapacityUtilization"


# Property: MetricDimension name/value requirements
@given(
    st.text(),
    st.text()
)
def test_metric_dimension_validation(name, value):
    """Test MetricDimension with various name/value combinations."""
    try:
        dim = appscaling.MetricDimension(
            Name=name,
            Value=value
        )
        dim_dict = dim.to_dict()
        
        # Both should be present as they're required
        assert "Name" in dim_dict
        assert "Value" in dim_dict
        assert dim_dict["Name"] == name
        assert dim_dict["Value"] == value
    except Exception as e:
        # Should not fail for any string inputs
        pytest.fail(f"MetricDimension failed with valid strings: {e}")


# Property: Test property override behavior
@given(
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=101, max_value=200)
)
def test_property_override(initial_value, new_value):
    """Test that properties can be updated after initial setting."""
    action = appscaling.ScalableTargetAction()
    
    # Set initial value
    action.MaxCapacity = initial_value
    assert action.MaxCapacity == initial_value
    
    # Override with new value
    action.MaxCapacity = new_value
    assert action.MaxCapacity == new_value
    
    # Check dict reflects latest value
    action_dict = action.to_dict()
    assert action_dict["MaxCapacity"] == new_value


# Property: Empty objects should produce minimal dicts
def test_empty_objects_minimal_dict():
    """Test that empty property objects produce minimal dictionaries."""
    # Object with all optional properties
    action = appscaling.ScalableTargetAction()
    action_dict = action.to_dict()
    
    # Should be empty dict if no properties set
    assert action_dict == {} or action_dict == {"Properties": {}}
    
    # Object with some required properties
    try:
        step = appscaling.StepAdjustment()
        # This should fail validation since ScalingAdjustment is required
        step_dict = step.to_dict()
    except Exception:
        # Expected to fail validation
        pass


# Property: List properties handling
@given(st.lists(
    st.integers(min_value=-100, max_value=100),
    min_size=1,
    max_size=10
))
def test_step_adjustments_list(adjustments):
    """Test StepScalingPolicyConfiguration with list of StepAdjustments."""
    steps = []
    for i, adj in enumerate(adjustments):
        step = appscaling.StepAdjustment(
            ScalingAdjustment=adj,
            MetricIntervalLowerBound=float(i * 10),
            MetricIntervalUpperBound=float((i + 1) * 10)
        )
        steps.append(step)
    
    config = appscaling.StepScalingPolicyConfiguration(
        StepAdjustments=steps
    )
    
    config_dict = config.to_dict()
    
    # Verify the list is properly serialized
    assert "StepAdjustments" in config_dict
    assert len(config_dict["StepAdjustments"]) == len(adjustments)
    
    for i, step_dict in enumerate(config_dict["StepAdjustments"]):
        assert step_dict["ScalingAdjustment"] == adjustments[i]
        assert step_dict["MetricIntervalLowerBound"] == float(i * 10)
        assert step_dict["MetricIntervalUpperBound"] == float((i + 1) * 10)


# Property: Test validation with AWS helper functions (Ref)
def test_ref_values_bypass_validation():
    """Test that Ref values bypass type validation."""
    from troposphere import Ref
    
    target = appscaling.ScalableTarget(
        "TestTarget",
        MaxCapacity=Ref("MaxCapacityParameter"),
        MinCapacity=1,
        ResourceId="table/MyTable",
        ScalableDimension="dynamodb:table:ReadCapacityUnits",
        ServiceNamespace="dynamodb"
    )
    
    target_dict = target.to_dict()
    
    # Ref should be preserved in the output
    assert target_dict["Properties"]["MaxCapacity"] == {"Ref": "MaxCapacityParameter"}
    assert target_dict["Properties"]["MinCapacity"] == 1


# Property: Test JSON serialization round-trip
@given(
    st.integers(min_value=1, max_value=1000),
    st.integers(min_value=1, max_value=1000),
    st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=50)
)
def test_json_serialization_roundtrip(max_cap, min_cap, resource_id):
    """Test that objects can be serialized to JSON and back."""
    target = appscaling.ScalableTarget(
        "TestTarget",
        MaxCapacity=max_cap,
        MinCapacity=min_cap,
        ResourceId=resource_id,
        ScalableDimension="test:dimension",
        ServiceNamespace="test"
    )
    
    # Convert to JSON
    json_str = target.to_json()
    
    # Parse back
    parsed = json.loads(json_str)
    
    # Verify structure preserved
    assert parsed["Type"] == "AWS::ApplicationAutoScaling::ScalableTarget"
    assert parsed["Properties"]["MaxCapacity"] == max_cap
    assert parsed["Properties"]["MinCapacity"] == min_cap
    assert parsed["Properties"]["ResourceId"] == resource_id


# Property: Test capacity constraints
@given(
    st.integers(),
    st.integers()
)
def test_capacity_values_any_integer(max_cap, min_cap):
    """Test that capacity values accept any integer (no built-in min/max validation)."""
    try:
        action = appscaling.ScalableTargetAction()
        action.MaxCapacity = max_cap
        action.MinCapacity = min_cap
        
        action_dict = action.to_dict()
        assert action_dict["MaxCapacity"] == max_cap
        assert action_dict["MinCapacity"] == min_cap
    except (ValueError, TypeError) as e:
        # The integer validator might reject some values
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])