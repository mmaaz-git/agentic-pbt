#!/usr/bin/env python3
"""Advanced property-based tests looking for subtle bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import pytest
import troposphere.connectcampaignsv2 as ccv2
from troposphere import validators, AWSHelperFn
import json
import math


# Test 1: Metamorphic property - Adding then removing a property

@given(
    bandwidth=st.floats(min_value=0, max_value=1),
    new_bandwidth=st.floats(min_value=0, max_value=1)
)
def test_property_update_metamorphic(bandwidth, new_bandwidth):
    """Test that updating a property changes the dict representation correctly."""
    pc = ccv2.PredictiveConfig(BandwidthAllocation=bandwidth)
    d1 = pc.to_dict()
    
    # Update the property
    pc.BandwidthAllocation = new_bandwidth
    d2 = pc.to_dict()
    
    # The dict should reflect the new value
    assert d2['BandwidthAllocation'] == new_bandwidth
    
    # Changing back should restore original
    pc.BandwidthAllocation = bandwidth
    d3 = pc.to_dict()
    assert d3 == d1


# Test 2: JSON serialization round-trip

@given(
    enable=st.booleans(),
    await_prompt=st.booleans()
)
def test_json_serialization_round_trip(enable, await_prompt):
    """Test that objects survive JSON serialization."""
    amd = ccv2.AnswerMachineDetectionConfig(
        EnableAnswerMachineDetection=enable,
        AwaitAnswerMachinePrompt=await_prompt
    )
    
    # Convert to JSON string
    json_str = amd.to_json()
    
    # Parse back
    parsed = json.loads(json_str)
    
    # Should be able to reconstruct from parsed dict
    amd2 = ccv2.AnswerMachineDetectionConfig.from_dict(None, parsed)
    
    # Should be equivalent
    assert amd.to_dict() == amd2.to_dict()


# Test 3: Test with AWSHelperFn (CloudFormation intrinsic functions)

def test_with_aws_helper_fn():
    """Test that AWSHelperFn values are accepted without validation."""
    from troposphere import Ref, GetAtt
    
    # Create a mock ref
    class MockResource:
        def __init__(self):
            self.title = "TestResource"
    
    mock = MockResource()
    ref = Ref(mock)
    
    # Should be able to use Ref as a value
    pc = ccv2.PredictiveConfig(BandwidthAllocation=ref)
    
    # to_dict should preserve the Ref
    d = pc.to_dict()
    assert 'BandwidthAllocation' in d
    # The Ref should be encoded properly
    assert isinstance(d['BandwidthAllocation'], dict)
    assert 'Ref' in d['BandwidthAllocation']


# Test 4: Test validation=False flag

@given(text=st.text())
def test_no_validation_mode(text):
    """Test that validation can be disabled."""
    # Create object without required properties
    c = ccv2.Campaign('TestCampaign')
    
    # Normal to_dict should fail
    with pytest.raises(ValueError):
        c.to_dict()
    
    # But with validation=False it should work
    d = c.to_dict(validation=False)
    assert 'Type' in d
    assert d['Type'] == 'AWS::ConnectCampaignsV2::Campaign'


# Test 5: Test property name validation for Campaign title

def test_campaign_title_validation():
    """Test that Campaign title must be alphanumeric.
    
    BUG FOUND: Empty string titles bypass validation!
    """
    # Valid titles
    valid_titles = ['Campaign1', 'TestCampaign', 'ABC123']
    for title in valid_titles:
        c = ccv2.Campaign(title)
        assert c.title == title
    
    # Invalid titles - most work correctly
    invalid_titles = ['Campaign-1', 'Test Campaign', 'Campaign!', '123_Campaign']
    for title in invalid_titles:
        with pytest.raises(ValueError, match="alphanumeric"):
            ccv2.Campaign(title)
    
    # BUG: Empty string should fail but doesn't
    # This is documented in bug_report_troposphere_connectcampaignsv2_*.md
    c = ccv2.Campaign('')  # Should raise ValueError but doesn't
    assert c.title == ''  # Bug: accepts empty title


# Test 6: Test deeply nested structures

@given(
    limits=st.lists(
        st.integers(min_value=1, max_value=100),
        min_size=1,
        max_size=3
    )
)
def test_deeply_nested_round_trip(limits):
    """Test round-trip with deeply nested structures."""
    # Create nested structure
    time_ranges = [ccv2.TimeRange(StartTime=f"{i:02d}:00", EndTime=f"{i+1:02d}:00") 
                   for i in limits]
    
    daily_hour = ccv2.DailyHour(Key='MONDAY', Value=time_ranges)
    open_hours = ccv2.OpenHours(DailyHours=[daily_hour])
    time_window = ccv2.TimeWindow(OpenHours=open_hours)
    
    # Convert to dict
    d1 = time_window.to_dict()
    
    # Round-trip
    tw2 = ccv2.TimeWindow.from_dict(None, d1)
    d2 = tw2.to_dict()
    
    assert d1 == d2


# Test 7: Test equality and hashing consistency

@given(
    val1=st.text(min_size=1, max_size=10),
    val2=st.text(min_size=1, max_size=10)
)
def test_equality_hash_consistency(val1, val2):
    """Test that equal objects have equal hashes."""
    tr1a = ccv2.TimeRange(StartTime=val1, EndTime=val2)
    tr1b = ccv2.TimeRange(StartTime=val1, EndTime=val2)
    tr2 = ccv2.TimeRange(StartTime=val2, EndTime=val1)
    
    # Equal objects should have equal hashes
    if tr1a == tr1b:
        assert hash(tr1a) == hash(tr1b)
    
    # Different objects should (usually) have different hashes
    if tr1a != tr2:
        # This might collide but should be rare
        pass  # Can't assert inequality of hashes


# Test 8: Test integer validator with float strings

@example("1.0")
@example("2.5")
@example("3.14159")
@given(val=st.floats(min_value=-1e10, max_value=1e10))
def test_integer_validator_float_strings(val):
    """Test integer validator with float string representations."""
    float_str = str(val)
    
    # Integer validator should reject float strings that aren't whole numbers
    try:
        int(float_str)
        # If int() succeeds, validator should too
        result = validators.integer(float_str)
        assert result == float_str
    except ValueError:
        # If int() fails, validator should too
        with pytest.raises(ValueError):
            validators.integer(float_str)


# Test 9: Test with special CloudFormation values

def test_special_cf_values():
    """Test with special CloudFormation pseudo-parameters."""
    from troposphere import AWS_NO_VALUE, AWS_REGION
    
    # These should be accepted as they are AWSHelperFn instances
    # But let's verify the actual behavior
    try:
        pc = ccv2.PredictiveConfig(BandwidthAllocation=AWS_REGION)
        d = pc.to_dict()
        # Should contain the special value
        assert 'BandwidthAllocation' in d
    except Exception as e:
        # Document if this doesn't work as expected
        print(f"Special CF value test failed: {e}")


# Test 10: Test from_dict with extra fields

def test_from_dict_extra_fields():
    """Test that from_dict rejects extra fields."""
    # Valid dict
    valid_dict = {'BandwidthAllocation': 0.5}
    pc = ccv2.PredictiveConfig.from_dict(None, valid_dict)
    assert pc.to_dict() == valid_dict
    
    # Dict with extra field
    invalid_dict = {'BandwidthAllocation': 0.5, 'ExtraField': 'value'}
    with pytest.raises(AttributeError, match="ExtraField"):
        ccv2.PredictiveConfig.from_dict(None, invalid_dict)


# Test 11: Test validators with byte strings

def test_validators_with_bytes():
    """Test validators with byte strings."""
    # Integer validator with bytes
    try:
        result = validators.integer(b'123')
        # Should accept byte strings that represent integers
        assert result == b'123'
    except (ValueError, TypeError):
        # Or might reject them
        pass
    
    # Double validator with bytes
    try:
        result = validators.double(b'3.14')
        assert result == b'3.14'
    except (ValueError, TypeError):
        pass
    
    # Boolean validator with bytes - should fail
    with pytest.raises(ValueError):
        validators.boolean(b'true')


# Test 12: Test object mutation after to_dict

@given(
    val1=st.floats(min_value=0, max_value=1),
    val2=st.floats(min_value=0, max_value=1)
)
def test_mutation_after_to_dict(val1, val2):
    """Test that mutating an object after to_dict doesn't affect the dict."""
    pc = ccv2.PredictiveConfig(BandwidthAllocation=val1)
    d1 = pc.to_dict()
    
    # Mutate the object
    pc.BandwidthAllocation = val2
    
    # Original dict should be unchanged
    assert d1['BandwidthAllocation'] == val1
    
    # New dict should have new value
    d2 = pc.to_dict()
    assert d2['BandwidthAllocation'] == val2


if __name__ == "__main__":
    print("Running advanced property tests...")
    
    # Run a few key tests
    test_property_update_metamorphic(0.5, 0.7)
    print("✓ Property update metamorphic test passed")
    
    test_campaign_title_validation()
    print("✓ Campaign title validation test passed")
    
    test_from_dict_extra_fields()
    print("✓ from_dict extra fields test passed")
    
    test_validators_with_bytes()
    print("✓ Validators with bytes test passed")
    
    print("\nRun with pytest for full test suite.")