import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import troposphere.cleanrooms as cleanrooms
from troposphere.validators import boolean, integer, double
from troposphere import AWSHelperFn
import pytest
import json


# Test edge cases with validator functions
@given(st.one_of(
    st.just("1.0"),
    st.just("0.0"),
    st.just(" 1 "),
    st.just(" 0 "),
    st.just("TRUE"),
    st.just("FALSE"),
    st.just("TrUe"),
    st.just("FaLsE")
))
def test_boolean_validator_edge_cases(value):
    """Test boolean validator with edge case string inputs."""
    # These should all fail since they're not in the exact accepted list
    with pytest.raises(ValueError):
        boolean(value)


@given(st.one_of(
    st.just(None),
    st.just([]),
    st.just({}),
    st.just(""),
    st.just(" ")
))
def test_validator_none_and_empty_inputs(value):
    """Test validators with None and empty inputs."""
    with pytest.raises(ValueError):
        boolean(value)
    
    with pytest.raises(ValueError):
        integer(value)
    
    with pytest.raises(ValueError):
        double(value)


# Test edge cases with property assignments
def test_property_type_coercion():
    """Test if properties are coerced or validated strictly."""
    # Test if boolean properties accept integer values
    obj = cleanrooms.DataEncryptionMetadata(
        AllowCleartext=1,  # Using 1 instead of True
        AllowDuplicates=0,  # Using 0 instead of False
        AllowJoinsOnColumnsWithDifferentNames="true",  # Using string
        PreserveNulls="false"  # Using string
    )
    d = obj.to_dict()
    
    # Check if values were converted to booleans
    assert d['AllowCleartext'] is True
    assert d['AllowDuplicates'] is False
    assert d['AllowJoinsOnColumnsWithDifferentNames'] is True
    assert d['PreserveNulls'] is False


# Test property validation with invalid types
def test_property_validation_type_mismatch():
    """Test that invalid property types are rejected."""
    # S3Location expects strings for Bucket and Key
    with pytest.raises(TypeError):
        cleanrooms.S3Location(Bucket=123, Key="valid-key").to_dict()
    
    with pytest.raises(TypeError):
        cleanrooms.S3Location(Bucket="valid-bucket", Key=None).to_dict()


# Test JSON serialization with special characters
@given(
    bucket=st.text(min_size=1).filter(lambda x: any(c in x for c in ['"', '\\', '\n', '\t'])),
    key=st.text(min_size=1).filter(lambda x: any(c in x for c in ['"', '\\', '\n', '\t']))
)
@settings(max_examples=50)
def test_json_serialization_special_chars(bucket, key):
    """Test JSON serialization with special characters."""
    obj = cleanrooms.S3Location(Bucket=bucket, Key=key)
    json_str = obj.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    assert parsed['Bucket'] == bucket
    assert parsed['Key'] == key


# Test validation with very large numbers
@given(
    minimum=st.one_of(
        st.floats(min_value=1e308, max_value=1.7e308, allow_nan=False, allow_infinity=False),
        st.floats(min_value=-1.7e308, max_value=-1e308, allow_nan=False, allow_infinity=False)
    )
)
def test_aggregation_constraint_large_numbers(minimum):
    """Test AggregationConstraint with very large numbers."""
    constraint = cleanrooms.AggregationConstraint(
        ColumnName="test",
        Minimum=minimum,
        Type="COUNT_DISTINCT"
    )
    d = constraint.to_dict()
    assert d['Minimum'] == minimum


# Test empty lists in properties that expect lists
def test_empty_list_properties():
    """Test properties that expect lists with empty lists."""
    # ReferencedTables requires a list - test with empty list
    schema = cleanrooms.AnalysisSchema(ReferencedTables=[])
    d = schema.to_dict()
    assert d['ReferencedTables'] == []
    
    # Test AnalysisRuleAggregation with empty lists
    rule = cleanrooms.AnalysisRuleAggregation(
        AggregateColumns=[],
        DimensionColumns=[],
        JoinColumns=[],
        OutputConstraints=[],
        ScalarFunctions=[]
    )
    d = rule.to_dict()
    assert d['AggregateColumns'] == []
    assert d['DimensionColumns'] == []


# Test unicode and emoji in string properties
@given(
    name=st.text(min_size=1).filter(lambda x: any(ord(c) > 127 for c in x)),
    param_type=st.sampled_from(['STRING', 'INTEGER', 'DECIMAL'])
)
@settings(max_examples=50)
def test_unicode_in_properties(name, param_type):
    """Test unicode characters in string properties."""
    obj = cleanrooms.AnalysisParameter(Name=name, Type=param_type)
    d = obj.to_dict()
    assert d['Name'] == name


# Test property name case sensitivity
def test_property_case_sensitivity():
    """Test if property names are case sensitive."""
    # Try to create S3Location with lowercase property names
    with pytest.raises(AttributeError):
        cleanrooms.S3Location(bucket="test", key="test")
    
    # Correct case should work
    obj = cleanrooms.S3Location(Bucket="test", Key="test")
    assert obj.to_dict()['Bucket'] == "test"


# Test setting properties after object creation
def test_property_modification_after_creation():
    """Test modifying properties after object creation."""
    obj = cleanrooms.S3Location(Bucket="initial", Key="initial")
    
    # Try to modify properties
    obj.Bucket = "modified"
    obj.Key = "modified"
    
    d = obj.to_dict()
    assert d['Bucket'] == "modified"
    assert d['Key'] == "modified"


# Test with None values for optional properties
@given(
    default=st.none()
)
def test_optional_property_explicit_none(default):
    """Test setting optional properties explicitly to None."""
    obj = cleanrooms.AnalysisParameter(
        Name="test",
        Type="STRING",
        DefaultValue=default
    )
    d = obj.to_dict()
    
    # None values should not appear in the dict
    assert 'DefaultValue' not in d


# Test nested object validation
def test_nested_object_type_validation():
    """Test that nested objects are validated for correct type."""
    # AnalysisTemplateArtifact expects S3Location for Location property
    with pytest.raises((TypeError, AttributeError)):
        # Try to pass a dict instead of S3Location object
        artifact = cleanrooms.AnalysisTemplateArtifact(
            Location={"Bucket": "test", "Key": "test"}
        )
        artifact.to_dict()


# Test integer validator with string representations
@given(
    value=st.one_of(
        st.just("1.0"),
        st.just("1e2"),
        st.just("0x10"),
        st.just("0b101"),
        st.just("0o17")
    )
)
def test_integer_validator_string_formats(value):
    """Test integer validator with various string number formats."""
    # These should fail as they're not simple integer strings
    with pytest.raises(ValueError):
        integer(value)


# Test double validator with special float values
@given(
    value=st.one_of(
        st.just(float('inf')),
        st.just(float('-inf')),
        st.just(float('nan'))
    )
)
def test_double_validator_special_floats(value):
    """Test double validator with special float values."""
    # These should pass through the double validator
    result = double(value)
    assert result == value or (value != value and result != result)  # Handle NaN


# Test from_dict with invalid structure
def test_from_dict_invalid_structure():
    """Test from_dict with invalid dictionary structure."""
    # Try to create from dict with missing required fields
    with pytest.raises((ValueError, KeyError, AttributeError)):
        cleanrooms.S3Location._from_dict(Bucket="test")  # Missing Key
    
    # Try with extra unknown fields
    with pytest.raises(AttributeError):
        cleanrooms.S3Location._from_dict(
            Bucket="test",
            Key="test",
            UnknownField="value"
        )


# Test equality and hashing
@given(
    bucket1=st.text(min_size=1, max_size=50),
    key1=st.text(min_size=1, max_size=50),
    bucket2=st.text(min_size=1, max_size=50),
    key2=st.text(min_size=1, max_size=50)
)
def test_object_equality_and_hash(bucket1, key1, bucket2, key2):
    """Test object equality and hashing."""
    obj1 = cleanrooms.S3Location(Bucket=bucket1, Key=key1)
    obj2 = cleanrooms.S3Location(Bucket=bucket1, Key=key1)
    obj3 = cleanrooms.S3Location(Bucket=bucket2, Key=key2)
    
    # Same properties should be equal
    if bucket1 == bucket2 and key1 == key2:
        assert obj1 == obj3
        assert hash(obj1) == hash(obj3)
    else:
        assert obj1 != obj3
    
    # Two objects with same properties should be equal
    assert obj1 == obj2
    assert hash(obj1) == hash(obj2)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])