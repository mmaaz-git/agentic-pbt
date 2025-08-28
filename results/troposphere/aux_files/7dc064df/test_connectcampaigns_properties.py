#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import assume, given, settings, strategies as st
import troposphere.connectcampaigns as cc
from troposphere import validators
import math
import re


# Test 1: Boolean validator handles various representations correctly
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator correctly handles documented valid inputs"""
    result = validators.boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


# Test 2: Double validator accepts float-convertible values
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text().filter(lambda x: x.replace('.', '', 1).replace('-', '', 1).replace('+', '', 1).replace('e', '', 1).replace('E', '', 1).isdigit() if x else False)
))
def test_double_validator_valid_inputs(value):
    """Test that double validator accepts valid numeric values"""
    try:
        float(value)
        can_convert = True
    except (ValueError, TypeError):
        can_convert = False
    
    if can_convert:
        result = validators.double(value)
        assert result == value


# Test 3: Required properties validation
@given(
    bandwidth=st.floats(min_value=0.1, max_value=1.0, allow_nan=False)
)
def test_predictive_dialer_required_property(bandwidth):
    """Test that PredictiveDialerConfig enforces required BandwidthAllocation"""
    # Should work with required property
    config = cc.PredictiveDialerConfig(BandwidthAllocation=bandwidth)
    assert config.properties["BandwidthAllocation"] == bandwidth
    
    # Validate that to_dict includes the property
    d = config.to_dict()
    assert "BandwidthAllocation" in d
    assert d["BandwidthAllocation"] == bandwidth


# Test 4: Title validation for alphanumeric only
@given(st.text(min_size=1))
def test_campaign_title_validation(title):
    """Test that Campaign titles must be alphanumeric"""
    is_alphanumeric = bool(re.match(r'^[a-zA-Z0-9]+$', title))
    
    if is_alphanumeric:
        # Should succeed with alphanumeric title
        campaign = cc.Campaign(
            title,
            ConnectInstanceArn="arn:aws:connect:us-east-1:123456789012:instance/test",
            DialerConfig=cc.DialerConfig(),
            Name="TestCampaign",
            OutboundCallConfig=cc.OutboundCallConfig(
                ConnectContactFlowArn="arn:aws:connect:us-east-1:123456789012:instance/test/flow/test"
            )
        )
        assert campaign.title == title
    else:
        # Should fail with non-alphanumeric title
        try:
            campaign = cc.Campaign(
                title,
                ConnectInstanceArn="arn:aws:connect:us-east-1:123456789012:instance/test",
                DialerConfig=cc.DialerConfig(),
                Name="TestCampaign",
                OutboundCallConfig=cc.OutboundCallConfig(
                    ConnectContactFlowArn="arn:aws:connect:us-east-1:123456789012:instance/test/flow/test"
                )
            )
            # If we get here, the validation didn't work as expected
            assert False, f"Expected ValueError for non-alphanumeric title: {title}"
        except ValueError as e:
            assert 'not alphanumeric' in str(e)


# Test 5: Property type validation
@given(
    dialing_capacity=st.one_of(
        st.floats(min_value=0.1, max_value=10.0, allow_nan=False),
        st.integers(min_value=1, max_value=10),
        st.text()
    )
)
def test_agentless_dialer_property_type_validation(dialing_capacity):
    """Test that properties validate their types correctly"""
    try:
        float(dialing_capacity)
        should_work = True
    except (ValueError, TypeError):
        should_work = False
    
    if should_work:
        config = cc.AgentlessDialerConfig(DialingCapacity=dialing_capacity)
        assert "DialingCapacity" in config.properties
    else:
        # Non-numeric values should raise an error
        try:
            config = cc.AgentlessDialerConfig(DialingCapacity=dialing_capacity)
            # If we get here without error, check if it's actually valid
            validators.double(dialing_capacity)
        except (ValueError, TypeError):
            pass  # Expected


# Test 6: to_dict/from_dict round-trip
@given(
    bandwidth=st.floats(min_value=0.1, max_value=1.0, allow_nan=False),
    capacity=st.floats(min_value=0.1, max_value=10.0, allow_nan=False)
)
def test_progressive_dialer_round_trip(bandwidth, capacity):
    """Test that objects survive to_dict/from_dict round-trip"""
    original = cc.ProgressiveDialerConfig(
        BandwidthAllocation=bandwidth,
        DialingCapacity=capacity
    )
    
    # Convert to dict
    d = original.to_dict()
    
    # Reconstruct from dict
    reconstructed = cc.ProgressiveDialerConfig._from_dict(**d)
    
    # Properties should match
    assert reconstructed.properties.get("BandwidthAllocation") == bandwidth
    assert reconstructed.properties.get("DialingCapacity") == capacity
    
    # Dicts should be equal
    assert original.to_dict() == reconstructed.to_dict()


# Test 7: DialerConfig mutual exclusivity
@given(
    bandwidth1=st.floats(min_value=0.1, max_value=1.0, allow_nan=False),
    bandwidth2=st.floats(min_value=0.1, max_value=1.0, allow_nan=False),
    capacity=st.floats(min_value=0.1, max_value=10.0, allow_nan=False)
)
def test_dialer_config_properties(bandwidth1, bandwidth2, capacity):
    """Test DialerConfig can hold different dialer configurations"""
    # Create configs
    predictive = cc.PredictiveDialerConfig(BandwidthAllocation=bandwidth1)
    progressive = cc.ProgressiveDialerConfig(BandwidthAllocation=bandwidth2)
    agentless = cc.AgentlessDialerConfig(DialingCapacity=capacity)
    
    # Test that DialerConfig can hold each type
    config1 = cc.DialerConfig(PredictiveDialerConfig=predictive)
    assert "PredictiveDialerConfig" in config1.properties
    
    config2 = cc.DialerConfig(ProgressiveDialerConfig=progressive)
    assert "ProgressiveDialerConfig" in config2.properties
    
    config3 = cc.DialerConfig(AgentlessDialerConfig=agentless)
    assert "AgentlessDialerConfig" in config3.properties


# Test 8: AnswerMachineDetectionConfig boolean properties
@given(
    await_prompt=st.booleans(),
    enable_detection=st.booleans()
)
def test_answer_machine_detection_booleans(await_prompt, enable_detection):
    """Test that AnswerMachineDetectionConfig correctly handles boolean properties"""
    config = cc.AnswerMachineDetectionConfig(
        EnableAnswerMachineDetection=enable_detection,
        AwaitAnswerMachinePrompt=await_prompt
    )
    
    # Check properties are set correctly
    assert config.properties["EnableAnswerMachineDetection"] == enable_detection
    assert config.properties.get("AwaitAnswerMachinePrompt") == await_prompt
    
    # Check serialization preserves booleans
    d = config.to_dict()
    assert d["EnableAnswerMachineDetection"] == enable_detection
    if await_prompt is not None:  # Optional property
        assert d.get("AwaitAnswerMachinePrompt") == await_prompt


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])