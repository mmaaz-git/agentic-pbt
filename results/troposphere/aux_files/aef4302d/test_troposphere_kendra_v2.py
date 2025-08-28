#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import troposphere.kendra as kendra
from troposphere.validators import integer, boolean, double
import troposphere
import pytest
import json

# Property 1: Validator conversion inconsistency between integer and double
@given(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x)))
def test_integer_vs_double_conversion_inconsistency(value):
    """Integer and double validators handle the same input differently"""
    # Integer validator preserves the original value
    int_result = integer(value)
    assert int_result == value
    assert type(int_result) == type(value)  # Preserves float type
    
    # Double validator preserves the original value too
    double_result = double(value)
    assert double_result == value
    assert type(double_result) == type(value)
    
    # But when used in classes, they behave the same
    # This inconsistency could be confusing

# Property 2: String integer preservation can lead to issues
@given(st.text(alphabet="0123456789", min_size=1, max_size=15))
def test_string_integer_preservation_issue(str_num):
    """String numbers are preserved as strings, not converted to integers"""
    result = integer(str_num)
    assert result == str_num
    assert type(result) == str
    
    # This means JSON serialization will have strings instead of numbers
    config = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=str_num,
        StorageCapacityUnits=str_num
    )
    
    dict_result = config.to_dict()
    # The values are strings, not integers
    assert type(dict_result['QueryCapacityUnits']) == str
    assert type(dict_result['StorageCapacityUnits']) == str
    
    # This could cause issues with CloudFormation expecting integers
    json_str = json.dumps(dict_result)
    parsed = json.loads(json_str)
    # Still strings after JSON round-trip
    assert type(parsed['QueryCapacityUnits']) == str

# Property 3: Leading zeros in string numbers
@given(st.integers(min_value=1, max_value=999))
def test_leading_zeros_preserved(num):
    """Leading zeros in string numbers are preserved"""
    str_with_zeros = "00" + str(num)
    
    result = integer(str_with_zeros)
    assert result == str_with_zeros
    assert result != str(num)
    
    # This can cause issues
    config = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=str_with_zeros,
        StorageCapacityUnits=num
    )
    
    dict_result = config.to_dict()
    # One has leading zeros, one doesn't
    assert dict_result['QueryCapacityUnits'] == str_with_zeros  # "00123"
    assert dict_result['StorageCapacityUnits'] == num  # 123

# Property 4: Boolean validator accepts unexpected inputs
@given(st.text(min_size=1, max_size=10))
def test_boolean_unexpected_inputs(text):
    """Boolean validator should only accept specific values"""
    if text not in ["true", "True", "false", "False", "0", "1"]:
        with pytest.raises(ValueError):
            boolean(text)

# Property 5: Empty strings handling
def test_empty_string_validators():
    """Test how validators handle empty strings"""
    # Integer validator with empty string
    with pytest.raises(ValueError):
        integer("")
    
    # Double validator with empty string
    with pytest.raises(ValueError):
        double("")
    
    # Boolean validator with empty string
    with pytest.raises(ValueError):
        boolean("")

# Property 6: Very large numbers
@given(st.integers(min_value=10**15, max_value=10**18))
def test_very_large_integers(large_num):
    """Test handling of very large integers"""
    result = integer(large_num)
    assert result == large_num
    
    # As string
    str_num = str(large_num)
    str_result = integer(str_num)
    assert str_result == str_num
    
    # In a class - might overflow in CloudFormation
    config = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=large_num,
        StorageCapacityUnits=large_num
    )
    assert config.to_dict()['QueryCapacityUnits'] == large_num

# Property 7: Special numeric strings
@given(st.sampled_from(["0x10", "0o10", "0b10", "1e5", "1.5e3", "+10", "-10"]))
def test_special_numeric_strings(special_str):
    """Test handling of special numeric string formats"""
    if special_str in ["+10", "-10"]:
        # These should work
        result = integer(special_str)
        assert result == special_str
    elif special_str in ["1e5", "1.5e3"]:
        # Scientific notation - integer validator will fail on these
        with pytest.raises(ValueError):
            integer(special_str)
        # But double should handle them
        double_result = double(special_str)
        assert double_result == special_str
    else:
        # Hex, octal, binary - should fail
        with pytest.raises(ValueError):
            integer(special_str)

# Property 8: Negative zero handling
def test_negative_zero():
    """Test handling of negative zero"""
    # Integer validator
    assert integer(0) == 0
    assert integer(-0) == 0  # Python treats -0 as 0
    assert integer("0") == "0"
    assert integer("-0") == "-0"  # String preserved!
    
    # This asymmetry could be problematic
    config1 = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=0,
        StorageCapacityUnits=-0
    )
    
    config2 = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits="0",
        StorageCapacityUnits="-0"
    )
    
    # Different representations
    dict1 = config1.to_dict()
    dict2 = config2.to_dict()
    
    assert dict1['QueryCapacityUnits'] == dict1['StorageCapacityUnits']  # Both 0
    assert dict2['QueryCapacityUnits'] != dict2['StorageCapacityUnits']  # "0" vs "-0"

# Property 9: Float strings with integer validator
@given(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)))
def test_float_strings_with_integer_validator(float_val):
    """Integer validator should reject float strings"""
    float_str = str(float_val)
    with pytest.raises(ValueError):
        integer(float_str)

# Property 10: Unicode digits
def test_unicode_digits():
    """Test handling of Unicode digit characters"""
    # Unicode digits like ၀၁၂၃ (Myanmar), ০১২৩ (Bengali)
    unicode_digits = ["୦", "௧", "၂", "໓", "༤", "᠕", "៦", "๗", "๘", "๙"]
    
    for digit in unicode_digits:
        # Should these work? They're valid Unicode digits
        with pytest.raises(ValueError) as exc_info:
            integer(digit)
        # They don't work - int() doesn't accept them

# Property 11: Type preservation in nested structures
@given(
    st.one_of(
        st.integers(min_value=0, max_value=100),
        st.text(alphabet="0123456789", min_size=1, max_size=3)
    )
)
def test_type_preservation_in_nested_structures(value):
    """Types should be preserved through nested structures"""
    # Create nested configuration
    acl = kendra.AccessControlListConfiguration(KeyPath="/path")
    
    config = kendra.WebCrawlerConfiguration(
        Urls=kendra.WebCrawlerUrls(
            SeedUrlConfiguration=kendra.WebCrawlerSeedUrlConfiguration(
                SeedUrls=["http://example.com"]
            )
        ),
        CrawlDepth=value  # integer validator
    )
    
    result = config.to_dict()
    
    # Type should be preserved
    if 'CrawlDepth' in result:
        assert result['CrawlDepth'] == value
        assert type(result['CrawlDepth']) == type(value)

if __name__ == "__main__":
    print("Running property-based tests for troposphere.kendra v2...")
    pytest.main([__file__, "-v", "--tb=short"])