#!/usr/bin/env python3
"""Additional edge case tests for troposphere.redshiftserverless."""

import troposphere.redshiftserverless as rs
from hypothesis import given, strategies as st, settings, assume
import pytest
import json


# Test edge case: Very large integers
@given(st.integers(min_value=2**31, max_value=2**63))
def test_integer_validator_large_values(value):
    """Test integer validator with very large values."""
    result = rs.integer(value)
    assert int(result) == value


# Test edge case: Negative integers
@given(st.integers(max_value=-1))
def test_integer_validator_negative(value):
    """Test integer validator with negative values."""
    result = rs.integer(value)
    assert int(result) == value


# Test edge case: Integer-like floats
@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x.is_integer()))
def test_integer_validator_whole_floats(value):
    """Test integer validator with floats that are whole numbers."""
    result = rs.integer(value)
    assert int(result) == int(value)


# Test edge case: Empty strings in properties
def test_empty_string_properties():
    """Test handling of empty strings in properties."""
    # Empty ParameterKey should work but may not be meaningful
    cp = rs.ConfigParameter(ParameterKey='', ParameterValue='value')
    assert cp.to_dict() == {'ParameterKey': '', 'ParameterValue': 'value'}
    
    # Empty ParameterValue should also work
    cp = rs.ConfigParameter(ParameterKey='key', ParameterValue='')
    assert cp.to_dict() == {'ParameterKey': 'key', 'ParameterValue': ''}


# Test edge case: Unicode in string properties
@given(st.text(alphabet=st.characters(min_codepoint=0x1F600, max_codepoint=0x1F64F), min_size=1, max_size=10))
def test_unicode_in_properties(emoji_text):
    """Test handling of unicode/emoji in string properties."""
    cp = rs.ConfigParameter(ParameterKey='emoji_key', ParameterValue=emoji_text)
    result = cp.to_dict()
    assert result['ParameterValue'] == emoji_text
    
    # Round-trip should preserve unicode
    cp2 = rs.ConfigParameter.from_dict('Test', result)
    assert cp2.to_dict() == result


# Test edge case: None values for optional properties
def test_none_optional_properties():
    """Test that optional properties can be None or omitted."""
    # Create Endpoint with only required fields
    endpoint = rs.Endpoint()
    result = endpoint.to_dict()
    # Should be empty dict or only have defined fields
    assert isinstance(result, dict)
    
    # Test with explicit None
    endpoint = rs.Endpoint(Address=None, Port=None)
    result = endpoint.to_dict()
    assert isinstance(result, dict)


# Test edge case: JSON serialization of complex nested structures
@given(
    st.lists(
        st.builds(
            rs.ConfigParameter,
            ParameterKey=st.text(min_size=1, max_size=20),
            ParameterValue=st.text(min_size=0, max_size=20)
        ),
        min_size=1,
        max_size=5
    )
)
def test_json_serialization(config_params):
    """Test that objects can be serialized to JSON."""
    wg = rs.Workgroup(
        'TestWorkgroup',
        WorkgroupName='test-wg',
        ConfigParameters=config_params
    )
    
    # to_json should produce valid JSON
    json_str = wg.to_json()
    parsed = json.loads(json_str)
    
    # Should have expected structure
    assert 'Type' in parsed
    assert 'Properties' in parsed
    
    # ConfigParameters should be preserved
    if config_params:
        assert len(parsed['Properties']['ConfigParameters']) == len(config_params)


# Test edge case: Special characters in property values
@given(st.text(alphabet='\n\r\t\x00\x01\x02', min_size=1, max_size=5))
def test_special_characters_in_values(special_text):
    """Test handling of special control characters."""
    try:
        cp = rs.ConfigParameter(ParameterKey='special', ParameterValue=special_text)
        result = cp.to_dict()
        # If it accepts it, should preserve exactly
        assert result['ParameterValue'] == special_text
    except (ValueError, TypeError):
        # Some special characters might be rejected
        pass


# Test edge case: from_dict with extra fields
def test_from_dict_extra_fields():
    """Test from_dict with unexpected extra fields."""
    data = {
        'ParameterKey': 'key',
        'ParameterValue': 'value',
        'ExtraField': 'should_be_ignored'
    }
    
    cp = rs.ConfigParameter.from_dict('Test', data)
    result = cp.to_dict()
    
    # Extra field should not appear in result
    assert 'ExtraField' not in result
    assert result == {'ParameterKey': 'key', 'ParameterValue': 'value'}


# Test edge case: from_dict with missing required fields
def test_from_dict_missing_fields():
    """Test from_dict with missing fields."""
    # Both fields are optional, so empty dict should work
    cp = rs.ConfigParameter.from_dict('Test', {})
    result = cp.to_dict()
    assert isinstance(result, dict)


# Test integer boundary values
def test_integer_validator_boundaries():
    """Test integer validator at common boundaries."""
    boundaries = [0, -1, 1, 2**31-1, -2**31, 2**32-1, 2**63-1, -2**63]
    
    for val in boundaries:
        try:
            result = rs.integer(val)
            assert int(result) == val
        except OverflowError:
            # Very large integers might overflow in some contexts
            pass


# Test boolean validator with numeric strings
@given(st.text(alphabet='01', min_size=2, max_size=10))
def test_boolean_numeric_strings(value):
    """Test boolean validator with strings like '00', '11', '01', etc."""
    try:
        result = rs.boolean(value)
        # Should only accept '0' and '1', not longer strings
        assert value in ['0', '1']
    except ValueError:
        # Expected for strings other than '0' and '1'
        assert value not in ['0', '1']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])