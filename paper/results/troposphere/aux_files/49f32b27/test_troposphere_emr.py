"""Property-based tests for troposphere.emr module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import math
from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the modules we're testing
from troposphere import emr
from troposphere.validators import emr as emr_validators


# Test 1: ScalingAdjustment percentage bounds property
@given(
    adjustment_type=st.sampled_from([
        emr_validators.CHANGE_IN_CAPACITY,
        emr_validators.PERCENT_CHANGE_IN_CAPACITY,
        emr_validators.EXACT_CAPACITY
    ]),
    scaling_adjustment=st.one_of(
        st.integers(min_value=-1000, max_value=1000),
        st.floats(min_value=-2.0, max_value=2.0, allow_nan=False, allow_infinity=False)
    )
)
def test_simple_scaling_policy_configuration_validation(adjustment_type, scaling_adjustment):
    """Test that SimpleScalingPolicyConfiguration validates ScalingAdjustment correctly based on AdjustmentType"""
    
    # Create SimpleScalingPolicyConfiguration object
    try:
        config = emr.SimpleScalingPolicyConfiguration(
            AdjustmentType=adjustment_type,
            ScalingAdjustment=scaling_adjustment
        )
        config.validate()
        
        # If validation passes, check the constraints are met
        if adjustment_type == emr_validators.PERCENT_CHANGE_IN_CAPACITY:
            # Should be between 0.0 and 1.0
            assert 0.0 <= float(scaling_adjustment) <= 1.0
        elif adjustment_type == emr_validators.EXACT_CAPACITY:
            # Should be positive integer
            assert int(scaling_adjustment) > 0
        # CHANGE_IN_CAPACITY accepts any integer
        
    except (ValueError, TypeError):
        # If validation fails, ensure it's for the right reason
        if adjustment_type == emr_validators.PERCENT_CHANGE_IN_CAPACITY:
            # Should fail if not between 0.0 and 1.0
            assert not (0.0 <= float(scaling_adjustment) <= 1.0)
        elif adjustment_type == emr_validators.EXACT_CAPACITY:
            # Should fail if not positive
            assert scaling_adjustment <= 0


# Test 2: Market validator property
@given(market_value=st.text())
def test_market_validator(market_value):
    """Test that market_validator only accepts 'ON_DEMAND' or 'SPOT'"""
    valid_values = ["ON_DEMAND", "SPOT"]
    
    try:
        result = emr_validators.market_validator(market_value)
        # If it doesn't raise, the value must be valid
        assert market_value in valid_values
        assert result == market_value
    except ValueError:
        # If it raises, the value must be invalid
        assert market_value not in valid_values


# Test 3: Volume type validator property
@given(volume_type=st.text())
def test_volume_type_validator(volume_type):
    """Test that volume_type_validator only accepts valid volume types"""
    valid_types = ["gp2", "gp3", "io1", "sc1", "st1", "standard"]
    
    try:
        result = emr_validators.volume_type_validator(volume_type)
        # If it doesn't raise, the value must be valid
        assert volume_type in valid_types
        assert result == volume_type
    except ValueError:
        # If it raises, the value must be invalid
        assert volume_type not in valid_types


# Test 4: AdditionalInfo validator property
@given(
    additional_info=st.one_of(
        st.dictionaries(st.text(), st.text()),
        st.dictionaries(st.integers(), st.text()),
        st.dictionaries(st.text(), st.integers()),
        st.lists(st.text()),
        st.text()
    )
)
def test_additional_info_validator(additional_info):
    """Test that additional_info_validator only accepts dict with string keys and values"""
    try:
        result = emr_validators.additional_info_validator(additional_info)
        # If it doesn't raise, it must be a dict with string keys and values
        assert isinstance(additional_info, dict)
        for k, v in additional_info.items():
            assert isinstance(k, str)
            assert isinstance(v, str)
        assert result == additional_info
    except (ValueError, AttributeError):
        # If it raises, it must violate the constraints
        if not isinstance(additional_info, dict):
            pass  # Expected to fail
        else:
            # Check if all keys and values are strings
            all_strings = all(isinstance(k, str) and isinstance(v, str) 
                              for k, v in additional_info.items())
            assert not all_strings


# Test 5: KeyValueClass initialization property
@given(
    key=st.one_of(st.none(), st.text()),
    value=st.one_of(st.none(), st.text()),
    extra_kwargs=st.dictionaries(
        st.text().filter(lambda x: x not in ["Key", "Value", "key", "value"]),
        st.text()
    )
)
def test_keyvalue_class_initialization(key, value, extra_kwargs):
    """Test that KeyValueClass properly initializes with key/value parameters"""
    
    # Prepare kwargs
    kwargs = extra_kwargs.copy()
    
    # Try to create KeyValueClass
    try:
        kv = emr_validators.KeyValueClass(key=key, value=value, **kwargs)
        
        # Check that key and value are properly set if provided
        if key is not None:
            assert kv.properties.get("Key") == key
        if value is not None:
            assert kv.properties.get("Value") == value
            
    except TypeError:
        # Should only fail if required properties are missing
        # Key and Value are required according to the props definition
        pass


# Test 6: ScalingConstraints property - MaxCapacity >= MinCapacity
@given(
    min_capacity=st.integers(min_value=0, max_value=10000),
    max_capacity=st.integers(min_value=0, max_value=10000)
)
def test_scaling_constraints_invariant(min_capacity, max_capacity):
    """Test that ScalingConstraints accepts any integer values for Min/MaxCapacity"""
    # This tests if the module properly creates ScalingConstraints
    # The AWS API would validate MaxCapacity >= MinCapacity, but the module might not
    
    try:
        constraints = emr.ScalingConstraints(
            MinCapacity=min_capacity,
            MaxCapacity=max_capacity
        )
        # The module accepts any values - it doesn't validate the relationship
        assert constraints.properties["MinCapacity"] == min_capacity
        assert constraints.properties["MaxCapacity"] == max_capacity
    except (ValueError, TypeError):
        # Should not raise for valid integers
        assert False, f"Unexpected error for min={min_capacity}, max={max_capacity}"


# Test 7: Configuration validator accepts Configuration objects or dicts
@given(
    configs=st.lists(
        st.one_of(
            st.builds(
                lambda: emr.Configuration(Classification="test"),
                # Using lambda to delay evaluation
            ),
            st.dictionaries(st.text(), st.text()),
            st.text(),  # Invalid type
            st.integers()  # Invalid type
        ),
        max_size=5
    )
)
def test_validate_configurations(configs):
    """Test that validate_configurations only accepts lists of Configuration or dict"""
    try:
        result = emr_validators.validate_configurations(configs)
        # If it doesn't raise, all items must be Configuration or dict
        assert isinstance(configs, list)
        for config in configs:
            assert isinstance(config, (emr.Configuration, dict))
        assert result == configs
    except TypeError:
        # If it raises, at least one item must be invalid
        if not isinstance(configs, list):
            pass  # Expected
        else:
            # Check if all items are valid types
            all_valid = all(isinstance(c, (emr.Configuration, dict)) for c in configs)
            assert not all_valid


# Test 8: ActionOnFailure validator for StepConfig
@given(action=st.text())
def test_action_on_failure_validator_step(action):
    """Test that action_on_failure_validator for Step only accepts valid actions"""
    valid_actions = ["CONTINUE", "CANCEL_AND_WAIT"]
    
    try:
        result = emr_validators.action_on_failure_validator(action)
        assert action in valid_actions
        assert result == action
    except ValueError:
        assert action not in valid_actions


# Test 9: OnDemandProvisioningSpecification allocation strategy
@given(strategy=st.text())
def test_on_demand_provisioning_allocation_strategy(strategy):
    """Test that OnDemandProvisioningSpecification only accepts 'lowest-price' allocation strategy"""
    valid_strategies = ["lowest-price"]
    
    try:
        spec = emr.OnDemandProvisioningSpecification(
            AllocationStrategy=strategy
        )
        spec.validate()
        assert strategy in valid_strategies
    except ValueError:
        assert strategy not in valid_strategies


# Test 10: SpotProvisioningSpecification allocation strategy
@given(
    strategy=st.one_of(st.none(), st.text()),
    timeout_action=st.sampled_from(["SWITCH_TO_ON_DEMAND", "TERMINATE_CLUSTER"]),
    timeout_minutes=st.integers(min_value=1, max_value=1440)
)
def test_spot_provisioning_allocation_strategy(strategy, timeout_action, timeout_minutes):
    """Test that SpotProvisioningSpecification validates allocation strategy correctly"""
    valid_strategies = ["capacity-optimized"]
    
    try:
        if strategy is None:
            # AllocationStrategy is optional
            spec = emr.SpotProvisioningSpecification(
                TimeoutAction=timeout_action,
                TimeoutDurationMinutes=timeout_minutes
            )
        else:
            spec = emr.SpotProvisioningSpecification(
                AllocationStrategy=strategy,
                TimeoutAction=timeout_action,
                TimeoutDurationMinutes=timeout_minutes
            )
        spec.validate()
        
        # If validation passes and strategy was provided, it must be valid
        if strategy is not None:
            assert strategy in valid_strategies
    except ValueError:
        # Should only fail if strategy is provided and invalid
        if strategy is not None:
            assert strategy not in valid_strategies