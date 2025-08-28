#!/usr/bin/env python3
"""Additional edge case tests for troposphere.customerprofiles."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.customerprofiles as cp
from troposphere import validators, AWSProperty, AWSObject
import pytest


# Edge case 1: Test if classes accept None for required fields and fail on to_dict()
@given(st.sampled_from([
    cp.AttributeItem,
    cp.AttributeDetails, 
    cp.ValueRange,
    cp.Threshold
]))
def test_none_for_required_fields(cls):
    """Test that None values for required fields cause proper validation errors."""
    # Get required fields from props
    required_fields = [k for k, (_, req) in cls.props.items() if req]
    
    if not required_fields:
        return  # Skip if no required fields
    
    # Create object with None for all required fields
    kwargs = {field: None for field in required_fields}
    obj = cls(**kwargs)
    
    # Should fail on to_dict() because None is not valid for required fields
    with pytest.raises((ValueError, TypeError)):
        obj.to_dict()


# Edge case 2: Test empty strings for required string fields
@given(st.data())
def test_empty_strings_for_required_string_fields(data):
    """Test that empty strings are handled properly for required string fields."""
    # Test AttributeItem which requires Name (string)
    item = cp.AttributeItem(Name="")
    # Empty string should be accepted (it's still a string)
    result = item.to_dict()
    assert result == {'Name': ''}
    
    # Test with various whitespace
    whitespace = data.draw(st.sampled_from([" ", "  ", "\t", "\n", " \t\n "]))
    item2 = cp.AttributeItem(Name=whitespace)
    result2 = item2.to_dict()
    assert result2 == {'Name': whitespace}


# Edge case 3: Test extreme integer values
@given(st.integers())
def test_extreme_integers_in_valuerange(value):
    """Test that ValueRange handles extreme integer values."""
    # Python integers have no limit, but let's see if the library handles them
    vr = cp.ValueRange(Start=value, End=value)
    result = vr.to_dict()
    assert result['Start'] == value
    assert result['End'] == value


# Edge case 4: Test property name collision with Python builtins
def test_property_name_collision():
    """Test if properties that might collide with Python builtins work correctly."""
    # The 'Object' property in various classes
    marketo = cp.MarketoSourceProperties(Object="Lead")
    result = marketo.to_dict()
    assert result == {'Object': 'Lead'}
    
    # Test we can still access the Python object class
    assert marketo.__class__.__bases__[0] == AWSProperty


# Edge case 5: Test circular references in nested structures
@given(st.text(min_size=1, max_size=10))
def test_no_circular_reference_protection(name):
    """Test if the library handles circular references (it likely doesn't need to for AWS resources)."""
    # Create a structure that references itself indirectly
    # This shouldn't be possible with the current API, but let's verify
    item = cp.AttributeItem(Name=name)
    
    # Try to set a property to itself (should fail or be ignored)
    try:
        item.SelfReference = item  # This property doesn't exist
    except AttributeError as e:
        assert "does not support attribute SelfReference" in str(e)


# Edge case 6: Test string coercion for integer fields
@given(st.text().filter(lambda x: x.isdigit() and len(x) < 100))
def test_string_integers_accepted(int_string):
    """Test that string representations of integers are accepted by integer validator."""
    if not int_string:  # Skip empty strings
        return
        
    # String integers should be accepted
    vr = cp.ValueRange(Start=int_string, End=int_string)
    result = vr.to_dict()
    # The value should remain as string (validator returns original value)
    assert result['Start'] == int_string
    assert result['End'] == int_string


# Edge case 7: Test unicode and special characters in string fields
@given(st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"])))
def test_unicode_in_string_fields(text):
    """Test that unicode characters are properly handled in string fields."""
    item = cp.AttributeItem(Name=text)
    result = item.to_dict()
    assert result['Name'] == text


# Edge case 8: Test validation bypass with no_validation()
def test_validation_bypass():
    """Test that no_validation() actually bypasses validation."""
    # Create object without required fields
    item = cp.AttributeItem()
    
    # Normal to_dict should fail
    with pytest.raises(ValueError) as exc_info:
        item.to_dict()
    assert "Resource Name required" in str(exc_info.value)
    
    # With validation=False it should work
    result = item.to_dict(validation=False)
    assert result == {}


# Edge case 9: Test float strings in integer fields
@given(st.floats(allow_nan=False, allow_infinity=False).map(str))
def test_float_strings_in_integer_fields(float_str):
    """Test that float strings fail integer validation appropriately."""
    try:
        vr = cp.ValueRange(Start=float_str, End=float_str)
        # If it succeeds, the float_str should be convertible to int
        int_value = int(float(float_str))
        # This means it was a whole number like "1.0"
        assert float(float_str) == int_value
    except ValueError as e:
        # Should fail for non-integer floats like "1.5"
        assert "not a valid integer" in str(e)


# Edge case 10: Test dictionary properties
def test_dict_properties():
    """Test classes with dict properties."""
    # ProfileAttributes has an 'Attributes' field that takes a dict
    pa = cp.ProfileAttributes(Attributes={"key1": "value1", "key2": "value2"})
    result = pa.to_dict()
    assert result['Attributes'] == {"key1": "value1", "key2": "value2"}
    
    # Test with nested dicts
    pa2 = cp.ProfileAttributes(Attributes={"nested": {"inner": "value"}})
    result2 = pa2.to_dict()
    assert result2['Attributes'] == {"nested": {"inner": "value"}}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])