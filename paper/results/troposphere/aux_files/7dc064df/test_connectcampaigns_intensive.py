#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import assume, given, settings, strategies as st, example
import troposphere.connectcampaigns as cc
from troposphere import validators
import math
import re


# More intensive testing with edge cases

# Test edge case: Empty string for double validator
@given(st.one_of(
    st.just(""),
    st.just(" "),
    st.just("\n"),
    st.just("\t"),
    st.text(alphabet=" \n\t\r", min_size=1)
))
def test_double_validator_empty_strings(value):
    """Test double validator with empty/whitespace strings"""
    try:
        validators.double(value)
        # If it doesn't raise, the string must be convertible to float
        float(value)
    except (ValueError, TypeError):
        pass  # Expected for invalid inputs


# Test extreme values for numeric properties
@given(st.one_of(
    st.just(float('inf')),
    st.just(float('-inf')),
    st.just(float('nan')),
    st.floats(min_value=1e308, max_value=1.7e308),  # Near float max
    st.floats(min_value=-1.7e308, max_value=-1e308),  # Near float min
))
def test_extreme_float_values(value):
    """Test handling of extreme float values"""
    if math.isnan(value) or math.isinf(value):
        # These might be rejected
        config = cc.AgentlessDialerConfig(DialingCapacity=value)
        # If accepted, they should be stored correctly
        assert config.properties.get("DialingCapacity") == value
    else:
        config = cc.AgentlessDialerConfig(DialingCapacity=value)
        assert config.properties["DialingCapacity"] == value


# Test boolean validator with unexpected types
@given(st.one_of(
    st.none(),
    st.lists(st.booleans()),
    st.dictionaries(st.text(), st.booleans()),
    st.floats(),
    st.complex_numbers()
))
def test_boolean_validator_invalid_types(value):
    """Test boolean validator rejects invalid types"""
    if value not in [True, False, 0, 1, "0", "1", "true", "false", "True", "False"]:
        try:
            result = validators.boolean(value)
            # Check if it's a valid conversion
            assert False, f"Unexpected success with {value}"
        except (ValueError, TypeError, AttributeError):
            pass  # Expected


# Test property setting with None values
@given(st.none())
def test_none_values_in_properties(value):
    """Test handling of None values in properties"""
    try:
        # Required property with None
        config = cc.PredictiveDialerConfig(BandwidthAllocation=value)
        # If it accepts None, check validation
        config.to_dict()
    except (ValueError, TypeError):
        pass  # Expected for None on required field


# Test Campaign with all properties
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=255),
    name=st.text(min_size=1, max_size=100),
    instance_arn=st.text(min_size=1).map(lambda x: f"arn:aws:connect:us-east-1:123456789012:instance/{x}"),
    flow_arn=st.text(min_size=1).map(lambda x: f"arn:aws:connect:us-east-1:123456789012:instance/test/flow/{x}"),
    bandwidth=st.floats(min_value=0.01, max_value=1.0, allow_nan=False),
    capacity=st.floats(min_value=0.01, max_value=100.0, allow_nan=False),
    enable_amd=st.booleans(),
    await_prompt=st.booleans()
)
@settings(max_examples=1000)
def test_campaign_full_construction(title, name, instance_arn, flow_arn, bandwidth, capacity, enable_amd, await_prompt):
    """Test full Campaign construction with all properties"""
    # Build components
    dialer_config = cc.DialerConfig(
        PredictiveDialerConfig=cc.PredictiveDialerConfig(
            BandwidthAllocation=bandwidth,
            DialingCapacity=capacity
        )
    )
    
    answer_config = cc.AnswerMachineDetectionConfig(
        EnableAnswerMachineDetection=enable_amd,
        AwaitAnswerMachinePrompt=await_prompt
    )
    
    outbound_config = cc.OutboundCallConfig(
        ConnectContactFlowArn=flow_arn,
        AnswerMachineDetectionConfig=answer_config
    )
    
    # Create campaign
    campaign = cc.Campaign(
        title,
        ConnectInstanceArn=instance_arn,
        DialerConfig=dialer_config,
        Name=name,
        OutboundCallConfig=outbound_config
    )
    
    # Verify all properties are set
    assert campaign.title == title
    assert campaign.properties["Name"] == name
    assert campaign.properties["ConnectInstanceArn"] == instance_arn
    
    # Test serialization
    d = campaign.to_dict()
    assert d["Type"] == "AWS::ConnectCampaigns::Campaign"
    assert d["Properties"]["Name"] == name
    
    # Test that from_dict works
    reconstructed = cc.Campaign.from_dict(title, d["Properties"])
    assert reconstructed.title == title
    assert reconstructed.properties["Name"] == name


# Test property mutation after creation
@given(
    initial_bandwidth=st.floats(min_value=0.1, max_value=0.5, allow_nan=False),
    new_bandwidth=st.floats(min_value=0.6, max_value=1.0, allow_nan=False)
)
def test_property_mutation(initial_bandwidth, new_bandwidth):
    """Test that properties can be modified after object creation"""
    config = cc.PredictiveDialerConfig(BandwidthAllocation=initial_bandwidth)
    assert config.properties["BandwidthAllocation"] == initial_bandwidth
    
    # Modify the property
    config.BandwidthAllocation = new_bandwidth
    assert config.properties["BandwidthAllocation"] == new_bandwidth
    
    # Verify serialization uses new value
    d = config.to_dict()
    assert d["BandwidthAllocation"] == new_bandwidth


# Test missing required properties
@given(st.floats(min_value=0.1, max_value=10.0, allow_nan=False))
def test_missing_required_property_validation(capacity):
    """Test that missing required properties are caught during validation"""
    # Create without required BandwidthAllocation
    config = cc.PredictiveDialerConfig()
    config.DialingCapacity = capacity
    
    # Should fail validation when converting to dict
    try:
        d = config.to_dict(validation=True)
        # If we get here, validation didn't catch missing required property
        assert False, "Expected validation error for missing BandwidthAllocation"
    except ValueError as e:
        assert "required" in str(e).lower()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])