#!/usr/bin/env python3
"""Property-based tests for troposphere.applicationautoscaling module."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import math

# Import the modules to test
from troposphere.validators import integer, double, boolean
from troposphere import applicationautoscaling as appscaling


# Property 1: integer validator accepts valid integers and rejects invalid ones
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False).map(lambda x: str(int(x))),
    st.text(alphabet='0123456789-', min_size=1)
))
def test_integer_validator_accepts_valid_integers(x):
    """Test that integer validator accepts valid integer representations."""
    try:
        result = integer(x)
        # If it succeeds, verify we can convert to int
        int_val = int(x)
        # Result should be the same as input (validator returns input unchanged)
        assert result == x
    except ValueError:
        # Should only fail for non-integer strings
        if isinstance(x, str):
            try:
                int(x)
                # If int() succeeds, integer() should have succeeded too
                assert False, f"integer() rejected valid integer string: {x}"
            except ValueError:
                # Both failed, which is correct
                pass


# Property 2: double validator accepts valid floats  
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False).map(str),
    st.integers().map(str)
))
def test_double_validator_accepts_valid_floats(x):
    """Test that double validator accepts valid float representations."""
    try:
        result = double(x)
        # If it succeeds, verify we can convert to float
        float_val = float(x)
        # Result should be the same as input
        assert result == x
    except ValueError:
        # Should only fail for non-numeric values
        try:
            float(x)
            assert False, f"double() rejected valid float: {x}"
        except (ValueError, TypeError):
            # Both failed, which is correct
            pass


# Property 3: boolean validator normalization is consistent
@given(st.sampled_from([
    True, False, 1, 0, "1", "0", 
    "true", "false", "True", "False"
]))
def test_boolean_validator_normalization(x):
    """Test that boolean validator consistently normalizes values."""
    result = boolean(x)
    
    # Check that the result is always a proper boolean
    assert isinstance(result, bool)
    
    # Check normalization is consistent
    if x in [True, 1, "1", "true", "True"]:
        assert result is True
    elif x in [False, 0, "0", "false", "False"]:
        assert result is False


# Property 4: ScalableTargetAction properties round-trip correctly
@given(
    st.one_of(st.none(), st.integers(min_value=0, max_value=10000)),
    st.one_of(st.none(), st.integers(min_value=0, max_value=10000))
)
def test_scalable_target_action_properties(max_cap, min_cap):
    """Test that ScalableTargetAction maintains properties correctly."""
    action = appscaling.ScalableTargetAction()
    
    # Set properties if not None
    if max_cap is not None:
        action.MaxCapacity = max_cap
    if min_cap is not None:
        action.MinCapacity = min_cap
    
    # Convert to dict
    action_dict = action.to_dict()
    
    # Check that set properties are in the dict
    if max_cap is not None:
        assert "MaxCapacity" in action_dict
        assert action_dict["MaxCapacity"] == max_cap
    if min_cap is not None:
        assert "MinCapacity" in action_dict
        assert action_dict["MinCapacity"] == min_cap


# Property 5: Required properties validation
@given(
    st.integers(min_value=1, max_value=10000),
    st.integers(min_value=1, max_value=10000),
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100)
)
def test_scalable_target_required_properties(max_cap, min_cap, resource_id, dimension, namespace):
    """Test that ScalableTarget enforces required properties."""
    # This should succeed with all required properties
    target = appscaling.ScalableTarget(
        "TestTarget",
        MaxCapacity=max_cap,
        MinCapacity=min_cap,
        ResourceId=resource_id,
        ScalableDimension=dimension,
        ServiceNamespace=namespace
    )
    
    # Convert to dict should work
    target_dict = target.to_dict()
    assert target_dict["Type"] == "AWS::ApplicationAutoScaling::ScalableTarget"
    assert target_dict["Properties"]["MaxCapacity"] == max_cap
    assert target_dict["Properties"]["MinCapacity"] == min_cap


# Property 6: StepAdjustment bounds relationship
@given(
    st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000)),
    st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000)),
    st.integers(min_value=-100, max_value=100)
)
def test_step_adjustment_bounds(lower_bound, upper_bound, adjustment):
    """Test StepAdjustment with metric interval bounds."""
    step = appscaling.StepAdjustment(ScalingAdjustment=adjustment)
    
    if lower_bound is not None:
        step.MetricIntervalLowerBound = lower_bound
    if upper_bound is not None:
        step.MetricIntervalUpperBound = upper_bound
    
    step_dict = step.to_dict()
    
    # Required property should always be present
    assert "ScalingAdjustment" in step_dict
    assert step_dict["ScalingAdjustment"] == adjustment
    
    # Optional properties should be present only if set
    if lower_bound is not None:
        assert "MetricIntervalLowerBound" in step_dict
        assert step_dict["MetricIntervalLowerBound"] == lower_bound
    else:
        assert "MetricIntervalLowerBound" not in step_dict
        
    if upper_bound is not None:
        assert "MetricIntervalUpperBound" in step_dict
        assert step_dict["MetricIntervalUpperBound"] == upper_bound
    else:
        assert "MetricIntervalUpperBound" not in step_dict


# Property 7: ScheduledAction time properties
@given(
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=50),
    st.one_of(st.none(), st.text(min_size=1, max_size=30)),
    st.one_of(st.none(), st.text(min_size=1, max_size=30)),
    st.one_of(st.none(), st.text(min_size=1, max_size=30))
)
def test_scheduled_action_properties(schedule, action_name, start_time, end_time, timezone):
    """Test ScheduledAction with various time-related properties."""
    action = appscaling.ScheduledAction(
        Schedule=schedule,
        ScheduledActionName=action_name
    )
    
    if start_time:
        action.StartTime = start_time
    if end_time:
        action.EndTime = end_time
    if timezone:
        action.Timezone = timezone
    
    action_dict = action.to_dict()
    
    # Required properties
    assert "Schedule" in action_dict
    assert action_dict["Schedule"] == schedule
    assert "ScheduledActionName" in action_dict
    assert action_dict["ScheduledActionName"] == action_name
    
    # Optional properties
    if start_time:
        assert action_dict.get("StartTime") == start_time
    if end_time:
        assert action_dict.get("EndTime") == end_time
    if timezone:
        assert action_dict.get("Timezone") == timezone


# Property 8: SuspendedState boolean flags
@given(
    st.one_of(st.none(), st.booleans()),
    st.one_of(st.none(), st.booleans()),
    st.one_of(st.none(), st.booleans())
)
def test_suspended_state_boolean_flags(scale_in, scale_out, scheduled):
    """Test SuspendedState with boolean suspension flags."""
    state = appscaling.SuspendedState()
    
    if scale_in is not None:
        state.DynamicScalingInSuspended = scale_in
    if scale_out is not None:
        state.DynamicScalingOutSuspended = scale_out
    if scheduled is not None:
        state.ScheduledScalingSuspended = scheduled
    
    state_dict = state.to_dict()
    
    # Check that only set properties are in the dict
    if scale_in is not None:
        assert "DynamicScalingInSuspended" in state_dict
        # Boolean validator should normalize to proper boolean
        assert state_dict["DynamicScalingInSuspended"] in [True, False]
    if scale_out is not None:
        assert "DynamicScalingOutSuspended" in state_dict
        assert state_dict["DynamicScalingOutSuspended"] in [True, False]
    if scheduled is not None:
        assert "ScheduledScalingSuspended" in state_dict
        assert state_dict["ScheduledScalingSuspended"] in [True, False]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])