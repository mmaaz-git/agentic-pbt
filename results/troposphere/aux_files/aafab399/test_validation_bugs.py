#!/usr/bin/env python3
"""Focused bug hunting for validation issues in troposphere.customerprofiles."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import troposphere.customerprofiles as cp
from troposphere import validators
import pytest


# BUG HUNT: Boolean validator accepts integer 1 and 0 but what about 2, -1, etc?
def test_boolean_validator_integer_edge_cases():
    """The boolean validator accepts 1 and 0, but what about other integers?"""
    print("Testing boolean validator with various integers:")
    
    test_values = [2, -1, 10, 100, -100, 999]
    
    for val in test_values:
        try:
            result = validators.boolean(val)
            print(f"  boolean({val}) = {result} (UNEXPECTED!)")
        except ValueError:
            print(f"  boolean({val}) = ValueError (expected)")
    
    # The code shows it only accepts 0 and 1, not other integers
    assert validators.boolean(0) is False
    assert validators.boolean(1) is True
    
    # These should fail
    with pytest.raises(ValueError):
        validators.boolean(2)
    with pytest.raises(ValueError):
        validators.boolean(-1)


# BUG HUNT: What happens with boolean strings that have different cases?
@given(st.sampled_from(["TRUE", "FALSE", "True", "False", "true", "false", "tRuE", "fAlSe"]))
def test_boolean_case_sensitivity(text):
    """Test case sensitivity of boolean validator."""
    try:
        result = validators.boolean(text)
        # According to the code, only "true", "True", "false", "False" are accepted
        assert text in ["true", "True", "false", "False"]
        if text in ["true", "True"]:
            assert result is True
        else:
            assert result is False
    except ValueError:
        # Should fail for mixed case like "tRuE"
        assert text not in ["true", "True", "false", "False"]


# BUG HUNT: Empty lists for list fields
def test_empty_list_validation():
    """Test if empty lists are accepted for list fields."""
    # MatchingRule expects a list of strings for Rule
    rule = cp.MatchingRule(Rule=[])
    result = rule.to_dict()
    assert result == {'Rule': []}
    
    # Is an empty list valid for AWS? This might be a semantic issue


# BUG HUNT: Test mutation of properties after creation
def test_property_mutation_after_creation():
    """Test if properties can be mutated after object creation."""
    item = cp.AttributeItem(Name="original")
    assert item.to_dict() == {'Name': 'original'}
    
    # Can we mutate it?
    item.Name = "modified"
    assert item.to_dict() == {'Name': 'modified'}
    
    # Can we delete it?
    del item.Name
    # Now to_dict should fail because Name is required
    with pytest.raises(ValueError) as exc_info:
        item.to_dict()
    assert "Resource Name required" in str(exc_info.value)


# BUG HUNT: What if we pass a class instance where a string is expected?
class CustomString:
    def __str__(self):
        return "custom_value"
    
    def __repr__(self):
        return "CustomString()"


def test_custom_object_as_string():
    """Test if custom objects with __str__ are accepted as strings."""
    custom = CustomString()
    
    try:
        item = cp.AttributeItem(Name=custom)
        # This should fail type checking
        assert False, "Should not accept non-string object"
    except TypeError as e:
        assert "expected <class 'str'>" in str(e)


# BUG HUNT: Validators with bytes
def test_validators_with_bytes():
    """Test if validators handle bytes correctly."""
    # Integer validator
    try:
        result = validators.integer(b"123")
        # bytes should work if they're numeric
        assert result == b"123"
        assert int(b"123") == 123
    except ValueError:
        assert False, "Should accept numeric bytes"
    
    # Non-numeric bytes
    with pytest.raises(ValueError):
        validators.integer(b"abc")
    
    # Double validator
    result = validators.double(b"123.45")
    assert result == b"123.45"
    assert float(b"123.45") == 123.45


# BUG HUNT: Integer validator with leading zeros
def test_integer_validator_leading_zeros():
    """Test integer validator with strings that have leading zeros."""
    # In Python 3, leading zeros are fine for int()
    result = validators.integer("0123")
    assert result == "0123"
    assert int("0123") == 123
    
    # But the original string is preserved
    vr = cp.ValueRange(Start="0123", End="0456")
    result = vr.to_dict()
    assert result == {'Start': '0123', 'End': '0456'}


# BUG HUNT: Integer validator with whitespace
@given(st.sampled_from([" 123", "123 ", " 123 ", "\t123", "123\n", "\r\n123\r\n"]))
def test_integer_validator_whitespace(text):
    """Test if integer validator handles whitespace correctly."""
    try:
        result = validators.integer(text)
        # If it succeeds, int() should handle the whitespace
        int_val = int(text)
        assert result == text  # Original preserved
    except ValueError:
        # If validator fails, int() should also fail
        with pytest.raises(ValueError):
            int(text)


# BUG HUNT: Test with __int__ and __float__ magic methods
class IntLike:
    def __int__(self):
        return 42
    
    def __index__(self):
        return 42


class FloatLike:
    def __float__(self):
        return 3.14
    
    def __index__(self):
        return 3


def test_validators_with_magic_methods():
    """Test if validators work with objects that have __int__ or __float__."""
    int_like = IntLike()
    float_like = FloatLike()
    
    # Integer validator
    result = validators.integer(int_like)
    assert result == int_like  # Should preserve the object
    assert int(int_like) == 42
    
    # Double validator  
    result = validators.double(float_like)
    assert result == float_like
    assert float(float_like) == 3.14


# BUG HUNT: Test setting properties to empty dict/list when not expected
def test_unexpected_empty_collections():
    """Test setting properties to empty collections when scalar expected."""
    # Try to set a string field to empty list
    try:
        item = cp.AttributeItem(Name=[])
        assert False, "Should not accept list for string field"
    except TypeError as e:
        assert "expected <class 'str'>" in str(e)
    
    # Try to set a string field to empty dict
    try:
        item = cp.AttributeItem(Name={})
        assert False, "Should not accept dict for string field"
    except TypeError as e:
        assert "expected <class 'str'>" in str(e)


if __name__ == "__main__":
    print("Running focused bug hunting tests...\n")
    
    test_boolean_validator_integer_edge_cases()
    print("\nTesting property mutation:")
    test_property_mutation_after_creation()
    print("  Property mutation works as expected")
    
    print("\nTesting custom objects as strings:")
    test_custom_object_as_string()
    print("  Custom objects correctly rejected")
    
    print("\nTesting validators with bytes:")
    test_validators_with_bytes()
    print("  Bytes handling works correctly")
    
    print("\nTesting validators with magic methods:")
    test_validators_with_magic_methods()
    print("  Magic methods work correctly")
    
    print("\nRunning all tests with pytest...")
    pytest.main([__file__, "-v", "--tb=short", "-q"])