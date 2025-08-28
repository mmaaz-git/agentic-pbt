#!/usr/bin/env python3
"""More intensive property-based tests to find edge case bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import pytest
import troposphere.connectcampaignsv2 as ccv2
from troposphere import validators
import math


# Edge case 1: Test with extreme float values

@given(val=st.floats())
def test_double_validator_edge_cases(val):
    """Test double validator with various float edge cases."""
    if math.isnan(val) or math.isinf(val):
        # NaN and Inf should pass validation - they are valid floats
        result = validators.double(val)
        assert result is val
    else:
        result = validators.double(val)
        assert result is val


@given(val=st.floats())
def test_bandwidth_allocation_with_edge_floats(val):
    """Test BandwidthAllocation with edge case floats."""
    # The property doesn't specify bounds, so all floats should work
    if not (math.isnan(val) or math.isinf(val)):
        pc = ccv2.PredictiveConfig(BandwidthAllocation=val)
        d = pc.to_dict()
        # Check that the value is preserved
        assert d['BandwidthAllocation'] == val or (math.isnan(d['BandwidthAllocation']) and math.isnan(val))


# Edge case 2: Test with special string values

@given(val=st.text())
def test_integer_validator_with_strings(val):
    """Test integer validator with various string inputs."""
    try:
        int(val)
        # If Python can convert it to int, the validator should accept it
        result = validators.integer(val)
        assert result == val  # Should preserve the string
    except (ValueError, TypeError):
        # If Python can't convert, validator should raise
        with pytest.raises(ValueError):
            validators.integer(val)


# Edge case 3: Test empty and None values

def test_empty_string_validators():
    """Test validators with empty strings."""
    # Empty string for integer
    with pytest.raises(ValueError):
        validators.integer("")
    
    # Empty string for double
    with pytest.raises(ValueError):
        validators.double("")
    
    # Empty string for boolean
    with pytest.raises(ValueError):
        validators.boolean("")


def test_none_validators():
    """Test validators with None."""
    with pytest.raises((ValueError, TypeError)):
        validators.integer(None)
    
    with pytest.raises((ValueError, TypeError)):
        validators.double(None)
    
    with pytest.raises(ValueError):
        validators.boolean(None)


# Edge case 4: Test with special numeric strings

@example("1.0")
@example("1e10")
@example("-0")
@example("+1")
@example("001")
@example("1_000")
@given(val=st.text(min_size=1))
def test_numeric_string_edge_cases(val):
    """Test validators with special numeric string formats."""
    # Test integer validator
    try:
        int(val)
        result = validators.integer(val)
        assert result == val
    except (ValueError, TypeError):
        with pytest.raises(ValueError):
            validators.integer(val)
    
    # Test double validator
    try:
        float(val)
        result = validators.double(val)
        assert result == val
    except (ValueError, TypeError):
        with pytest.raises(ValueError):
            validators.double(val)


# Edge case 5: Test object equality and hashing

@given(
    bandwidth1=st.floats(min_value=0, max_value=1),
    bandwidth2=st.floats(min_value=0, max_value=1)
)
def test_object_equality(bandwidth1, bandwidth2):
    """Test that objects with same properties are equal."""
    pc1 = ccv2.PredictiveConfig(BandwidthAllocation=bandwidth1)
    pc2 = ccv2.PredictiveConfig(BandwidthAllocation=bandwidth1)
    pc3 = ccv2.PredictiveConfig(BandwidthAllocation=bandwidth2)
    
    # Same values should be equal
    assert pc1 == pc2
    
    # Different values should not be equal
    if bandwidth1 != bandwidth2 and not (math.isnan(bandwidth1) and math.isnan(bandwidth2)):
        assert pc1 != pc3


# Edge case 6: Test with very long strings

@given(long_string=st.text(min_size=1000, max_size=10000))
def test_long_string_properties(long_string):
    """Test properties with very long strings."""
    # TimeRange accepts string times
    tr = ccv2.TimeRange(StartTime=long_string, EndTime=long_string)
    d = tr.to_dict()
    assert d['StartTime'] == long_string
    assert d['EndTime'] == long_string
    
    # Round-trip should work
    tr2 = ccv2.TimeRange.from_dict(None, d)
    d2 = tr2.to_dict()
    assert d == d2


# Edge case 7: Test list properties with empty lists

def test_empty_list_properties():
    """Test list properties with empty lists."""
    cls = ccv2.CommunicationLimits(CommunicationLimitList=[])
    d = cls.to_dict()
    assert d == {'CommunicationLimitList': []}
    
    # Round-trip
    cls2 = ccv2.CommunicationLimits.from_dict(None, d)
    d2 = cls2.to_dict()
    assert d == d2


# Edge case 8: Test nested object round-trips with empty optional fields

def test_nested_with_optional_fields():
    """Test nested objects where optional fields are omitted."""
    # Create TelephonyOutboundConfig without optional AnswerMachineDetectionConfig
    toc = ccv2.TelephonyOutboundConfig(
        ConnectContactFlowId='flow-123'
        # ConnectSourcePhoneNumber is optional
        # AnswerMachineDetectionConfig is optional
    )
    d = toc.to_dict()
    
    # Should only have the required field
    assert 'ConnectContactFlowId' in d
    assert 'ConnectSourcePhoneNumber' not in d
    assert 'AnswerMachineDetectionConfig' not in d
    
    # Round-trip
    toc2 = ccv2.TelephonyOutboundConfig.from_dict(None, d)
    d2 = toc2.to_dict()
    assert d == d2


# Edge case 9: Test with Unicode and special characters

@given(text=st.text(alphabet=st.characters(min_codepoint=0x1F600, max_codepoint=0x1F64F)))  # Emojis
def test_unicode_in_string_properties(text):
    """Test that Unicode/emoji characters work in string properties."""
    if not text:  # Skip empty strings
        return
    
    tr = ccv2.TimeRange(StartTime=text, EndTime=text)
    d = tr.to_dict()
    assert d['StartTime'] == text
    assert d['EndTime'] == text
    
    # Round-trip
    tr2 = ccv2.TimeRange.from_dict(None, d)
    d2 = tr2.to_dict()
    assert d == d2


# Edge case 10: Test boolean validator with numeric edge cases

def test_boolean_numeric_edge_cases():
    """Test boolean validator with numeric edge cases."""
    # Only 0 and 1 should work for integers
    assert validators.boolean(0) is False
    assert validators.boolean(1) is True
    
    # Other integers should fail
    with pytest.raises(ValueError):
        validators.boolean(2)
    
    with pytest.raises(ValueError):
        validators.boolean(-1)
    
    # Floats 0.0 and 1.0 work due to Python's equality (0.0 == 0 is True)
    assert validators.boolean(0.0) is False
    assert validators.boolean(1.0) is True
    
    # Other floats should fail
    with pytest.raises(ValueError):
        validators.boolean(0.5)
    
    with pytest.raises(ValueError):
        validators.boolean(1.5)


if __name__ == "__main__":
    print("Running edge case tests...")
    import traceback
    
    # Run specific tests that might reveal bugs
    try:
        test_boolean_numeric_edge_cases()
        print("✓ Boolean numeric edge cases passed")
    except Exception as e:
        print(f"✗ Boolean numeric edge cases FAILED: {e}")
        traceback.print_exc()
    
    try:
        test_empty_string_validators()
        print("✓ Empty string validators passed")
    except Exception as e:
        print(f"✗ Empty string validators FAILED: {e}")
    
    try:
        test_none_validators()
        print("✓ None validators passed")
    except Exception as e:
        print(f"✗ None validators FAILED: {e}")
    
    print("\nRun with pytest for full test suite.")