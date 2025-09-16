#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.kendra as kendra
from troposphere.validators import integer, boolean, double
import pytest

# Property 1: Boolean validator normalization is idempotent
@given(st.one_of(
    st.booleans(),
    st.sampled_from([0, 1, "0", "1", "true", "false", "True", "False"])
))
def test_boolean_validator_idempotent(value):
    """The boolean validator should be idempotent - applying it twice should give the same result"""
    try:
        result1 = boolean(value)
        result2 = boolean(result1)
        assert result1 == result2
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)
    except ValueError:
        # If it fails once, it should always fail
        with pytest.raises(ValueError):
            boolean(value)

# Property 2: Integer validator preserves the original type for valid inputs
@given(st.one_of(
    st.integers(),
    st.text(alphabet="0123456789", min_size=1),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x))
))
def test_integer_validator_preserves_type(value):
    """The integer validator returns the original value, not converted to int"""
    try:
        result = integer(value)
        # The validator should return the original value, not convert it
        assert result == value
        assert type(result) == type(value)
    except ValueError:
        # Should only fail for truly invalid inputs
        pytest.fail(f"integer validator failed for {value}")

# Property 3: Integer validator with string numbers
@given(st.integers(min_value=-10000, max_value=10000))
def test_integer_validator_string_conversion(num):
    """Integer validator should accept string representation of integers"""
    str_num = str(num)
    result = integer(str_num)
    # It returns the string, not the integer
    assert result == str_num
    assert type(result) == str
    # But it should be convertible to the same integer
    assert int(result) == num

# Property 4: Double validator type conversion
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(alphabet="0123456789.", min_size=1).filter(lambda x: x.count('.') <= 1 and x != '.')
))
def test_double_validator_behavior(value):
    """The double validator should accept float-convertible values"""
    try:
        result = double(value)
        # Should return the original value
        assert result == value
        # Should be convertible to float
        float(result)
    except ValueError:
        # Should only fail for non-numeric strings
        with pytest.raises(ValueError):
            float(value)

# Property 5: CapacityUnitsConfiguration with various integer inputs
@given(
    query_units=st.one_of(
        st.integers(min_value=0, max_value=1000),
        st.text(alphabet="0123456789", min_size=1, max_size=4)
    ),
    storage_units=st.one_of(
        st.integers(min_value=0, max_value=1000),
        st.text(alphabet="0123456789", min_size=1, max_size=4)
    )
)
def test_capacity_units_accepts_various_integer_types(query_units, storage_units):
    """CapacityUnitsConfiguration should accept integers and numeric strings"""
    config = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=query_units,
        StorageCapacityUnits=storage_units
    )
    
    result = config.to_dict()
    assert 'QueryCapacityUnits' in result
    assert 'StorageCapacityUnits' in result
    
    # Values should be preserved as-is
    assert result['QueryCapacityUnits'] == query_units
    assert result['StorageCapacityUnits'] == storage_units

# Property 6: Boolean fields normalization
@given(
    st.sampled_from([True, False, 0, 1, "0", "1", "true", "false", "True", "False"])
)
def test_boolean_field_normalization(bool_value):
    """Boolean fields should normalize various truthy/falsy values"""
    target = kendra.DocumentAttributeTarget(
        TargetDocumentAttributeKey="test_key",
        TargetDocumentAttributeValueDeletion=bool_value
    )
    
    result = target.to_dict()
    deletion_value = result.get('TargetDocumentAttributeValueDeletion')
    
    # Should be normalized to True or False
    assert isinstance(deletion_value, bool)
    
    # Check normalization is correct
    if bool_value in [True, 1, "1", "true", "True"]:
        assert deletion_value == True
    elif bool_value in [False, 0, "0", "false", "False"]:
        assert deletion_value == False

# Property 7: Required fields must be provided
@given(st.integers())
def test_required_fields_validation(value):
    """Classes should enforce required fields"""
    # CapacityUnitsConfiguration requires both QueryCapacityUnits and StorageCapacityUnits
    with pytest.raises((TypeError, AttributeError)):
        # Missing StorageCapacityUnits
        kendra.CapacityUnitsConfiguration(QueryCapacityUnits=value)
    
    with pytest.raises((TypeError, AttributeError)):
        # Missing QueryCapacityUnits
        kendra.CapacityUnitsConfiguration(StorageCapacityUnits=value)
    
    # Both provided should work
    config = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=value,
        StorageCapacityUnits=value
    )
    assert config.to_dict()['QueryCapacityUnits'] == value

# Property 8: Lists should be preserved
@given(st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5))
def test_list_fields_preserved(string_list):
    """List fields should preserve the list structure"""
    config = kendra.ConfluenceSpaceConfiguration(
        ExcludeSpaces=string_list
    )
    
    result = config.to_dict()
    if string_list:  # Only included if non-empty
        assert 'ExcludeSpaces' in result
        assert result['ExcludeSpaces'] == string_list
        assert isinstance(result['ExcludeSpaces'], list)

# Property 9: Nested properties
@given(st.text(min_size=1, max_size=20))
def test_nested_property_structure(key_path):
    """Nested property classes should maintain structure"""
    acl_config = kendra.AccessControlListConfiguration(KeyPath=key_path)
    
    result = acl_config.to_dict()
    assert 'KeyPath' in result
    assert result['KeyPath'] == key_path
    
    # Use in parent class
    s3_config = kendra.S3DataSourceConfiguration(
        BucketName="test-bucket",
        AccessControlListConfiguration=acl_config
    )
    
    s3_result = s3_config.to_dict()
    assert 'AccessControlListConfiguration' in s3_result
    assert s3_result['AccessControlListConfiguration']['KeyPath'] == key_path

# Property 10: Integer validator edge cases
@given(st.one_of(
    st.just(0),
    st.just(-0),
    st.just("0"),
    st.just("-0"),
    st.floats(min_value=-1e10, max_value=1e10).filter(lambda x: x == int(x)),
))
def test_integer_validator_edge_cases(value):
    """Integer validator should handle edge cases like 0, -0, and whole floats"""
    result = integer(value)
    assert result == value
    # Should be convertible to int
    int(result)

if __name__ == "__main__":
    print("Running property-based tests for troposphere.kendra...")
    pytest.main([__file__, "-v", "--tb=short"])