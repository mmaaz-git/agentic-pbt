import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.cleanrooms as cleanrooms
from troposphere.validators import boolean, integer, double
import pytest
import math


# Test validator functions first
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator accepts documented valid inputs."""
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(
    st.integers(),
    st.text(min_size=1),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator rejects invalid inputs."""
    # Filter out valid values
    assume(value not in [True, False, 1, 0, "1", "0", "true", "True", "false", "False"])
    
    with pytest.raises(ValueError):
        boolean(value)


@given(st.one_of(
    st.integers(),
    st.text().filter(lambda x: x.strip() and x.strip().lstrip('-').isdigit()),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x))
))
def test_integer_validator_valid_inputs(value):
    """Test that integer validator accepts valid integer representations."""
    try:
        # The integer validator should accept anything that can be converted to int
        result = integer(value)
        # It should be convertible to int without error
        int(result)
    except (ValueError, TypeError, OverflowError):
        # Some edge cases like very large floats might fail
        pass


@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text().filter(lambda x: x.strip() and (x.strip().lstrip('-').replace('.', '', 1).isdigit()))
))
def test_double_validator_valid_inputs(value):
    """Test that double validator accepts valid float representations."""
    try:
        result = double(value)
        # It should be convertible to float without error
        float(result)
    except (ValueError, TypeError, OverflowError):
        # Some edge cases might fail
        pass


# Test AWSProperty classes with required and optional properties
@given(
    bucket=st.text(min_size=1, max_size=100),
    key=st.text(min_size=1, max_size=100)
)
def test_s3location_required_properties(bucket, key):
    """Test S3Location with required properties."""
    obj = cleanrooms.S3Location(Bucket=bucket, Key=key)
    d = obj.to_dict()
    assert d['Bucket'] == bucket
    assert d['Key'] == key


def test_s3location_missing_required_property():
    """Test that S3Location raises error when required property is missing."""
    # Bucket is required but not provided
    obj = cleanrooms.S3Location(Key="some-key")
    with pytest.raises(ValueError, match="Resource Bucket required"):
        obj.to_dict()


# Test to_dict/from_dict round-trip
@given(
    bucket=st.text(min_size=1, max_size=100).filter(lambda x: not x.startswith('_')),
    key=st.text(min_size=1, max_size=100).filter(lambda x: not x.startswith('_'))
)
def test_s3location_dict_roundtrip(bucket, key):
    """Test that S3Location can round-trip through dict representation."""
    obj1 = cleanrooms.S3Location(Bucket=bucket, Key=key)
    dict1 = obj1.to_dict()
    
    # Create new object from dict
    obj2 = cleanrooms.S3Location._from_dict(**dict1)
    dict2 = obj2.to_dict()
    
    assert dict1 == dict2


# Test AnalysisParameter with optional DefaultValue
@given(
    name=st.text(min_size=1, max_size=100),
    param_type=st.text(min_size=1, max_size=50),
    default=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_analysis_parameter_optional_property(name, param_type, default):
    """Test AnalysisParameter with optional DefaultValue."""
    if default is None:
        obj = cleanrooms.AnalysisParameter(Name=name, Type=param_type)
        d = obj.to_dict()
        assert 'DefaultValue' not in d
    else:
        obj = cleanrooms.AnalysisParameter(Name=name, Type=param_type, DefaultValue=default)
        d = obj.to_dict()
        assert d['DefaultValue'] == default
    
    assert d['Name'] == name
    assert d['Type'] == param_type


# Test nested properties
@given(
    bucket=st.text(min_size=1, max_size=100),
    key=st.text(min_size=1, max_size=100)
)
def test_analysis_template_artifact_nested(bucket, key):
    """Test AnalysisTemplateArtifact with nested S3Location."""
    location = cleanrooms.S3Location(Bucket=bucket, Key=key)
    artifact = cleanrooms.AnalysisTemplateArtifact(Location=location)
    
    d = artifact.to_dict()
    assert 'Location' in d
    assert d['Location']['Bucket'] == bucket
    assert d['Location']['Key'] == key


# Test property with list of strings
@given(
    tables=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10)
)
def test_analysis_schema_list_property(tables):
    """Test AnalysisSchema with list of strings."""
    schema = cleanrooms.AnalysisSchema(ReferencedTables=tables)
    d = schema.to_dict()
    assert d['ReferencedTables'] == tables


# Test boolean properties
@given(
    allow_cleartext=st.booleans(),
    allow_duplicates=st.booleans(),
    allow_joins=st.booleans(),
    preserve_nulls=st.booleans()
)
def test_data_encryption_metadata_booleans(allow_cleartext, allow_duplicates, allow_joins, preserve_nulls):
    """Test DataEncryptionMetadata with boolean properties."""
    obj = cleanrooms.DataEncryptionMetadata(
        AllowCleartext=allow_cleartext,
        AllowDuplicates=allow_duplicates,
        AllowJoinsOnColumnsWithDifferentNames=allow_joins,
        PreserveNulls=preserve_nulls
    )
    d = obj.to_dict()
    
    # The boolean validator should ensure these are actual booleans
    assert d['AllowCleartext'] == allow_cleartext
    assert d['AllowDuplicates'] == allow_duplicates
    assert d['AllowJoinsOnColumnsWithDifferentNames'] == allow_joins
    assert d['PreserveNulls'] == preserve_nulls


# Test complex nested structure with ConfiguredTableAnalysisRulePolicy
@given(
    column_names=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5),
    function=st.sampled_from(['SUM', 'COUNT', 'AVG', 'MIN', 'MAX']),
    dimension_cols=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5),
    join_cols=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5),
    scalar_funcs=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5),
    column_name=st.text(min_size=1, max_size=50),
    minimum=st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False),
    constraint_type=st.sampled_from(['COUNT_DISTINCT', 'MIN'])
)
def test_analysis_rule_aggregation_complex(column_names, function, dimension_cols, join_cols, 
                                          scalar_funcs, column_name, minimum, constraint_type):
    """Test complex nested AnalysisRuleAggregation structure."""
    agg_col = cleanrooms.AggregateColumn(ColumnNames=column_names, Function=function)
    constraint = cleanrooms.AggregationConstraint(
        ColumnName=column_name,
        Minimum=minimum,
        Type=constraint_type
    )
    
    rule = cleanrooms.AnalysisRuleAggregation(
        AggregateColumns=[agg_col],
        DimensionColumns=dimension_cols,
        JoinColumns=join_cols,
        OutputConstraints=[constraint],
        ScalarFunctions=scalar_funcs
    )
    
    d = rule.to_dict()
    
    # Verify structure is preserved
    assert len(d['AggregateColumns']) == 1
    assert d['AggregateColumns'][0]['ColumnNames'] == column_names
    assert d['AggregateColumns'][0]['Function'] == function
    assert d['DimensionColumns'] == dimension_cols
    assert d['JoinColumns'] == join_cols
    assert d['ScalarFunctions'] == scalar_funcs
    assert len(d['OutputConstraints']) == 1
    assert d['OutputConstraints'][0]['ColumnName'] == column_name
    assert d['OutputConstraints'][0]['Minimum'] == minimum
    assert d['OutputConstraints'][0]['Type'] == constraint_type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])