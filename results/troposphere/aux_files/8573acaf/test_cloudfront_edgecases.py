"""Edge case tests for troposphere.cloudfront module - looking for bugs"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings, example
import pytest

# Import the modules we're testing
from troposphere import cloudfront, validators
from troposphere.validators import cloudfront as cf_validators
from troposphere import Tag, Tags


# Test 1: Check if integer validator accepts strings that are clearly not integers
@given(st.text().filter(lambda x: not x.strip().lstrip('-').isdigit()))
def test_integer_non_numeric_strings(s):
    """Integer validator should reject non-numeric strings"""
    with pytest.raises(ValueError, match="is not a valid integer"):
        validators.integer(s)


# Test 2: Check boundary condition in network_port error message
def test_network_port_error_message_accuracy():
    """Test if network_port error message is accurate"""
    # The error says "between 0 and 65535" but the code checks for >= -1
    # Let's test -1 specifically
    result = validators.network_port(-1)
    assert result == -1  # -1 should be allowed
    
    # Test the error message accuracy
    try:
        validators.network_port(-2)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        # The error message says "between 0 and 65535" but -1 is actually allowed
        # This is a minor documentation bug
        assert "between 0 and 65535" in str(e)


# Test 3: Boolean validator with integer types other than 0 and 1
@given(st.integers().filter(lambda x: x not in [0, 1]))
def test_boolean_with_other_integers(n):
    """Boolean should only accept 0 and 1 as integers, not other values"""
    with pytest.raises(ValueError):
        validators.boolean(n)


# Test 4: Test validate_tags_items_array with empty Items list
def test_tags_empty_items():
    """Test validate_tags_items_array with empty Items list"""
    # Empty list should be valid
    result = cf_validators.validate_tags_items_array({"Items": []})
    assert result == {"Items": []}


# Test 5: Double validator with special float values
def test_double_special_values():
    """Test double validator with NaN and Inf"""
    # Regular float should work
    assert validators.double(3.14) == 3.14
    
    # String inf/nan
    assert validators.double("inf") == "inf"
    assert validators.double("-inf") == "-inf" 
    assert validators.double("nan") == "nan"
    
    # Python float inf/nan
    float_inf = float('inf')
    assert validators.double(float_inf) == float_inf
    
    float_nan = float('nan')
    assert validators.double(float_nan) == float_nan


# Test 6: Test that boolean "1" string vs integer 1 behave the same
def test_boolean_string_vs_int_one():
    """Test that '1' string and 1 integer both map to True"""
    assert validators.boolean("1") is True
    assert validators.boolean(1) is True
    assert validators.boolean("1") == validators.boolean(1)


# Test 7: Case variations in boolean strings
@given(st.sampled_from(["TRUE", "True", "true", "TrUe", "FALSE", "False", "false", "FaLsE"]))
def test_boolean_case_variations(s):
    """Test various case combinations for true/false strings"""
    if s.lower() == "true":
        if s in ["True", "true"]:
            assert validators.boolean(s) is True
        else:
            # Other variations like "TRUE", "TrUe" should fail
            with pytest.raises(ValueError):
                validators.boolean(s)
    elif s.lower() == "false":
        if s in ["False", "false"]:
            assert validators.boolean(s) is False
        else:
            # Other variations like "FALSE", "FaLsE" should fail
            with pytest.raises(ValueError):
                validators.boolean(s)


# Test 8: Method validator with duplicate values
def test_methods_with_duplicates():
    """Test access control methods with duplicate values"""
    methods = ["GET", "POST", "GET", "DELETE", "POST"]
    # Should accept duplicates
    result = cf_validators.cloudfront_access_control_allow_methods(methods)
    assert result == methods


# Test 9: Testing validators with byte strings
def test_validators_with_bytes():
    """Test how validators handle byte strings"""
    
    # Integer validator with bytes
    result = validators.integer(b"123")
    assert result == b"123"
    
    # Double validator with bytes  
    result = validators.double(b"3.14")
    assert result == b"3.14"


# Test 10: Network port with string representations
@given(st.integers(min_value=-1, max_value=65535).map(str))
def test_network_port_string_numbers(port_str):
    """Test network_port with string representations of valid ports"""
    result = validators.network_port(port_str)
    assert result == port_str


# Test 11: Tags validation with mixed types
def test_tags_validation_mixed():
    """Test more complex scenarios for tags validation"""
    
    # Create valid Tag objects
    tag1 = Tag("Key1", "Value1")
    tag2 = Tag("Key2", "Value2")
    
    # Valid case
    valid_tags = {"Items": [tag1, tag2]}
    result = cf_validators.validate_tags_items_array(valid_tags)
    assert result == valid_tags
    
    # Mixed with non-Tag objects
    with pytest.raises(ValueError, match="Items array in Tags must contain Tag objects"):
        cf_validators.validate_tags_items_array({"Items": [tag1, "not a tag", tag2]})


# Test 12: Test that required properties are enforced
def test_required_properties():
    """Test that required properties raise errors when missing"""
    
    # DefaultCacheBehavior requires TargetOriginId and ViewerProtocolPolicy
    with pytest.raises(TypeError):
        # Missing required properties
        cloudfront.DefaultCacheBehavior()
    
    # With only one required property
    with pytest.raises(TypeError):
        cloudfront.DefaultCacheBehavior(TargetOriginId="origin1")
    
    # With both required properties - should work
    behavior = cloudfront.DefaultCacheBehavior(
        TargetOriginId="origin1",
        ViewerProtocolPolicy="allow-all"
    )
    assert behavior.TargetOriginId == "origin1"


# Test 13: Whitespace in enum values
@given(st.sampled_from(["none", "whitelist", "allExcept", "all"]))
def test_enum_with_whitespace(valid_value):
    """Test enum validators with whitespace around valid values"""
    # With leading/trailing whitespace - should fail
    with pytest.raises(ValueError):
        cf_validators.cloudfront_cache_cookie_behavior(f" {valid_value} ")
    
    with pytest.raises(ValueError):
        cf_validators.cloudfront_cache_cookie_behavior(f"\t{valid_value}")
    
    with pytest.raises(ValueError):
        cf_validators.cloudfront_cache_cookie_behavior(f"{valid_value}\n")


# Test 14: Test integer validator with very long numeric strings
@given(st.integers(min_value=10**100, max_value=10**200))
def test_integer_huge_numbers(huge_num):
    """Test integer validator with astronomically large numbers"""
    # Python handles arbitrary precision integers
    result = validators.integer(huge_num)
    assert result == huge_num
    
    # Also test as string
    result_str = validators.integer(str(huge_num))
    assert result_str == str(huge_num)


# Test 15: CloudFront frame options only has 2 valid values
def test_frame_options_limited():
    """Test that frame options only accepts DENY and SAMEORIGIN"""
    valid = ["DENY", "SAMEORIGIN"]
    
    for v in valid:
        assert cf_validators.cloudfront_frame_option(v) == v
    
    # X-Frame-Options typically also supports ALLOW-FROM but CloudFront doesn't
    with pytest.raises(ValueError, match="FrameOption must be of"):
        cf_validators.cloudfront_frame_option("ALLOW-FROM https://example.com")
    
    # Lower case should fail
    with pytest.raises(ValueError):
        cf_validators.cloudfront_frame_option("deny")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])