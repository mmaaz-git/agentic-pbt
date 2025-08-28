#!/usr/bin/env python3
"""Property-based tests for troposphere.connectcampaignsv2 module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import troposphere.connectcampaignsv2 as ccv2
from troposphere import validators


# Test 1: Round-trip property for AWSProperty classes
# Property: from_dict(to_dict(obj)) should produce equivalent dictionaries

@given(bandwidth=st.floats(min_value=0.0, max_value=1.0))
def test_predictive_config_round_trip(bandwidth):
    """Test that PredictiveConfig survives round-trip through dict conversion."""
    obj = ccv2.PredictiveConfig(BandwidthAllocation=bandwidth)
    d1 = obj.to_dict()
    obj2 = ccv2.PredictiveConfig.from_dict(None, d1)
    d2 = obj2.to_dict()
    assert d1 == d2, f"Round-trip failed: {d1} != {d2}"


@given(bandwidth=st.floats(min_value=0.0, max_value=1.0))
def test_progressive_config_round_trip(bandwidth):
    """Test that ProgressiveConfig survives round-trip through dict conversion."""
    obj = ccv2.ProgressiveConfig(BandwidthAllocation=bandwidth)
    d1 = obj.to_dict()
    obj2 = ccv2.ProgressiveConfig.from_dict(None, d1)
    d2 = obj2.to_dict()
    assert d1 == d2, f"Round-trip failed: {d1} != {d2}"


@given(
    enable=st.booleans(),
    await_prompt=st.booleans()
)
def test_answer_machine_detection_config_round_trip(enable, await_prompt):
    """Test that AnswerMachineDetectionConfig survives round-trip."""
    obj = ccv2.AnswerMachineDetectionConfig(
        EnableAnswerMachineDetection=enable,
        AwaitAnswerMachinePrompt=await_prompt
    )
    d1 = obj.to_dict()
    obj2 = ccv2.AnswerMachineDetectionConfig.from_dict(None, d1)
    d2 = obj2.to_dict()
    assert d1 == d2, f"Round-trip failed: {d1} != {d2}"


@given(
    frequency=st.integers(min_value=1, max_value=100),
    max_count=st.integers(min_value=1, max_value=100),
    unit=st.sampled_from(['DAY', 'WEEK', 'MONTH'])
)
def test_communication_limit_round_trip(frequency, max_count, unit):
    """Test that CommunicationLimit survives round-trip."""
    obj = ccv2.CommunicationLimit(
        Frequency=frequency,
        MaxCountPerRecipient=max_count,
        Unit=unit
    )
    d1 = obj.to_dict()
    obj2 = ccv2.CommunicationLimit.from_dict(None, d1)
    d2 = obj2.to_dict()
    assert d1 == d2, f"Round-trip failed: {d1} != {d2}"


@given(
    start_time=st.text(min_size=1, max_size=10),
    end_time=st.text(min_size=1, max_size=10)
)
def test_time_range_round_trip(start_time, end_time):
    """Test that TimeRange survives round-trip."""
    obj = ccv2.TimeRange(StartTime=start_time, EndTime=end_time)
    d1 = obj.to_dict()
    obj2 = ccv2.TimeRange.from_dict(None, d1)
    d2 = obj2.to_dict()
    assert d1 == d2, f"Round-trip failed: {d1} != {d2}"


# Test 2: Validator properties
# These validators are documented to accept certain values

def test_boolean_validator_conversions():
    """Test that boolean validator converts expected values correctly."""
    # From the source code, these are the exact accepted values
    true_values = [True, 1, "1", "true", "True"]
    false_values = [False, 0, "0", "false", "False"]
    
    for val in true_values:
        result = validators.boolean(val)
        assert result is True, f"boolean({val!r}) should return True, got {result}"
    
    for val in false_values:
        result = validators.boolean(val)
        assert result is False, f"boolean({val!r}) should return False, got {result}"


@given(val=st.one_of(
    st.booleans(),
    st.sampled_from([0, 1]),
    st.sampled_from(["0", "1", "true", "false", "True", "False"])
))
def test_boolean_validator_idempotence(val):
    """Test that applying boolean validator twice gives same result."""
    try:
        result1 = validators.boolean(val)
        result2 = validators.boolean(result1)
        assert result1 == result2, f"boolean validator not idempotent for {val}"
    except ValueError:
        # If it raises ValueError once, it should always raise
        with pytest.raises(ValueError):
            validators.boolean(val)


@given(val=st.text(min_size=1))
def test_boolean_validator_invalid_values(val):
    """Test that invalid values raise ValueError."""
    # Skip valid values
    if val in [True, False, 1, 0, "1", "0", "true", "false", "True", "False"]:
        return
    
    with pytest.raises(ValueError):
        validators.boolean(val)


@given(val=st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(alphabet=st.characters(categories=['Nd']), min_size=1)  # Numeric strings
))
def test_integer_validator_preserves_type(val):
    """Test that integer validator preserves the input type when valid."""
    try:
        # Convert text to see if it's a valid integer string
        if isinstance(val, str):
            int(val)  # This will raise if not valid
        elif isinstance(val, float) and val != val // 1:
            # Skip non-integer floats
            return
        
        result = validators.integer(val)
        assert result is val, f"integer validator should preserve input, got {result!r} from {val!r}"
        assert type(result) == type(val), f"integer validator changed type from {type(val)} to {type(result)}"
    except (ValueError, TypeError):
        # Should raise for invalid inputs
        with pytest.raises(ValueError):
            validators.integer(val)


@given(val=st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=1).filter(lambda s: s.replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '').isdigit())
))
def test_double_validator_preserves_type(val):
    """Test that double validator preserves the input type when valid."""
    try:
        # Check if it's a valid float string
        if isinstance(val, str):
            float(val)  # This will raise if not valid
        
        result = validators.double(val)
        assert result is val, f"double validator should preserve input, got {result!r} from {val!r}"
        assert type(result) == type(val), f"double validator changed type from {type(val)} to {type(result)}"
    except (ValueError, TypeError):
        # Should raise for invalid inputs
        with pytest.raises(ValueError):
            validators.double(val)


# Test 3: Required property validation

def test_campaign_requires_properties():
    """Test that Campaign validation fails without required properties."""
    # Campaign has these required properties: Name, ConnectInstanceId, ChannelSubtypeConfig
    c = ccv2.Campaign('TestCampaign')
    
    # Should not raise during creation
    assert c.title == 'TestCampaign'
    
    # Should raise during to_dict() validation
    with pytest.raises(ValueError, match="required"):
        c.to_dict()


@given(
    name=st.text(min_size=1),
    instance_id=st.text(min_size=1)
)
def test_campaign_missing_channel_config(name, instance_id):
    """Test that Campaign requires ChannelSubtypeConfig."""
    c = ccv2.Campaign(
        'TestCampaign',
        Name=name,
        ConnectInstanceId=instance_id
        # Missing ChannelSubtypeConfig
    )
    
    with pytest.raises(ValueError, match="ChannelSubtypeConfig.*required"):
        c.to_dict()


# Test 4: Type checking property

def test_type_checking_immediate():
    """Test that type checking happens immediately on property assignment."""
    pc = ccv2.PredictiveConfig(BandwidthAllocation=0.5)
    
    # Should accept valid types
    pc.BandwidthAllocation = 0.7
    pc.BandwidthAllocation = 1
    pc.BandwidthAllocation = "0.3"  # String that can be converted to float
    
    # Should reject invalid types - ValueError is raised by the validator
    with pytest.raises(ValueError):
        ccv2.PredictiveConfig(BandwidthAllocation={})  # Dict is not a valid double


@given(
    invalid_value=st.one_of(
        st.dictionaries(st.text(), st.text()),
        st.lists(st.integers()),
        st.none()
    )
)
def test_bandwidth_allocation_type_checking(invalid_value):
    """Test that BandwidthAllocation rejects invalid types."""
    with pytest.raises((TypeError, ValueError)):
        ccv2.PredictiveConfig(BandwidthAllocation=invalid_value)


# Test 5: List properties with nested objects

@given(
    limits=st.lists(
        st.builds(
            lambda f, m, u: {
                'Frequency': f,
                'MaxCountPerRecipient': m, 
                'Unit': u
            },
            f=st.integers(min_value=1, max_value=100),
            m=st.integers(min_value=1, max_value=100),
            u=st.sampled_from(['DAY', 'WEEK', 'MONTH'])
        ),
        min_size=0,
        max_size=5
    )
)
def test_communication_limits_list_round_trip(limits):
    """Test that CommunicationLimits with list of limits survives round-trip."""
    # Create CommunicationLimit objects from dicts
    limit_objs = [ccv2.CommunicationLimit(**l) for l in limits]
    
    cls = ccv2.CommunicationLimits(CommunicationLimitList=limit_objs)
    d1 = cls.to_dict()
    cls2 = ccv2.CommunicationLimits.from_dict(None, d1)
    d2 = cls2.to_dict()
    assert d1 == d2, f"Round-trip failed for list property"


if __name__ == "__main__":
    # Run a quick smoke test
    print("Running property-based tests for troposphere.connectcampaignsv2...")
    test_boolean_validator_conversions()
    print("✓ Boolean validator conversions test passed")
    test_campaign_requires_properties()
    print("✓ Campaign required properties test passed")
    test_type_checking_immediate()
    print("✓ Type checking immediate test passed")
    print("\nAll smoke tests passed! Run with pytest for full test suite.")