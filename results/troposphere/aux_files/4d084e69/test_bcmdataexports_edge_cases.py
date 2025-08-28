import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.bcmdataexports as bcm
import pytest
import json


@st.composite
def valid_string_strategy(draw):
    """Generate valid non-empty strings for AWS properties"""
    return draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip() != ""))


# Test edge case: Empty strings for required properties
@given(
    empty_str=st.just(""),
    whitespace_str=st.sampled_from(["   ", "\t", "\n", "  \n  "])
)
def test_empty_strings_for_required_properties(empty_str, whitespace_str):
    """Test that empty or whitespace-only strings are accepted for required string properties"""
    # The code doesn't seem to validate that strings are non-empty
    # Let's see if this causes issues
    
    # Test with empty string
    try:
        data_query1 = bcm.DataQuery(QueryStatement=empty_str)
        dict1 = data_query1.to_dict()
        assert dict1["QueryStatement"] == empty_str
    except (ValueError, TypeError) as e:
        # If it raises an error, that's actually good validation
        pass
    
    # Test with whitespace
    try:
        data_query2 = bcm.DataQuery(QueryStatement=whitespace_str)
        dict2 = data_query2.to_dict()
        assert dict2["QueryStatement"] == whitespace_str
    except (ValueError, TypeError) as e:
        pass


# Test edge case: Unicode and special characters
@given(
    unicode_str=st.text(
        alphabet=st.characters(min_codepoint=0x1F600, max_codepoint=0x1F64F),  # Emojis
        min_size=1,
        max_size=10
    ).filter(lambda x: x != ""),
    special_chars=st.text(
        alphabet="!@#$%^&*(){}[]|\\:;\"'<>?,./`~",
        min_size=1,
        max_size=20
    )
)
def test_unicode_and_special_characters(unicode_str, special_chars):
    """Test that unicode and special characters are handled correctly"""
    # S3 bucket names have restrictions, but the troposphere library might not validate them
    
    # Test unicode in query statements
    data_query = bcm.DataQuery(QueryStatement=unicode_str)
    dict_repr = data_query.to_dict()
    assert dict_repr["QueryStatement"] == unicode_str
    
    # Test special characters
    data_query2 = bcm.DataQuery(QueryStatement=special_chars)
    dict_repr2 = data_query2.to_dict()
    assert dict_repr2["QueryStatement"] == special_chars


# Test edge case: Very long strings
@given(
    long_string=st.text(min_size=10000, max_size=100000)
)
@settings(max_examples=10)  # Fewer examples due to size
def test_very_long_strings(long_string):
    """Test that very long strings are handled correctly"""
    assume(long_string != "")
    
    data_query = bcm.DataQuery(QueryStatement=long_string)
    dict_repr = data_query.to_dict()
    
    # Verify the long string is preserved
    assert dict_repr["QueryStatement"] == long_string
    assert len(dict_repr["QueryStatement"]) == len(long_string)


# Test edge case: Property deletion after creation
@given(
    query=valid_string_strategy(),
    table_configs=st.dictionaries(
        valid_string_strategy(),
        st.dictionaries(valid_string_strategy(), valid_string_strategy(), max_size=3),
        max_size=3
    )
)
def test_property_deletion_behavior(query, table_configs):
    """Test what happens when we delete properties after setting them"""
    assume(len(table_configs) > 0)
    
    data_query = bcm.DataQuery(QueryStatement=query)
    data_query.TableConfigurations = table_configs
    
    # Verify it's set
    dict_before = data_query.to_dict()
    assert "TableConfigurations" in dict_before
    
    # Try to delete the optional property
    del data_query.TableConfigurations
    
    # Check if deletion worked
    dict_after = data_query.to_dict()
    # The property might still be in the dict but with None value
    # or it might be completely removed


# Test edge case: None values for optional properties
@given(
    query=valid_string_strategy()
)
def test_none_values_for_optional_properties(query):
    """Test that None values are handled correctly for optional properties"""
    data_query = bcm.DataQuery(QueryStatement=query)
    
    # Try setting optional property to None
    data_query.TableConfigurations = None
    
    dict_repr = data_query.to_dict()
    # Check how None is represented
    assert "QueryStatement" in dict_repr
    # TableConfigurations might be absent or None


# Test edge case: Invalid property names
@given(
    query=valid_string_strategy(),
    invalid_prop_name=st.text(min_size=1, max_size=50).filter(
        lambda x: x not in ["QueryStatement", "TableConfigurations"] and x != ""
    )
)
def test_invalid_property_names(query, invalid_prop_name):
    """Test that setting invalid properties raises appropriate errors"""
    data_query = bcm.DataQuery(QueryStatement=query)
    
    # Try to set a property that doesn't exist
    with pytest.raises(AttributeError):
        setattr(data_query, invalid_prop_name, "some_value")


# Test edge case: Modifying nested objects after assignment
@given(
    compression1=st.sampled_from(["GZIP", "PARQUET"]),
    compression2=st.sampled_from(["GZIP", "PARQUET"]),
)
def test_nested_object_modification(compression1, compression2):
    """Test that modifying nested objects works correctly"""
    assume(compression1 != compression2)
    
    s3_config = bcm.S3OutputConfigurations(
        Compression=compression1,
        Format="PARQUET",
        OutputType="S3",
        Overwrite="CREATE_NEW_REPORT"
    )
    
    s3_dest = bcm.S3Destination(
        S3Bucket="bucket",
        S3OutputConfigurations=s3_config,
        S3Prefix="prefix",
        S3Region="us-east-1"
    )
    
    # Get initial state
    dict_before = s3_dest.to_dict()
    assert dict_before["S3OutputConfigurations"]["Compression"] == compression1
    
    # Modify the nested object
    s3_config.Compression = compression2
    
    # Check if the change propagates
    dict_after = s3_dest.to_dict()
    assert dict_after["S3OutputConfigurations"]["Compression"] == compression2


# Test edge case: JSON serialization round-trip
@given(
    name=valid_string_strategy(),
    frequency=st.sampled_from(["SYNCHRONOUS", "ASYNCHRONOUS"])
)
def test_json_serialization_roundtrip(name, frequency):
    """Test that objects can be serialized to JSON and back"""
    # Create a complex nested structure
    data_query = bcm.DataQuery(QueryStatement="SELECT * FROM table")
    refresh = bcm.RefreshCadence(Frequency=frequency)
    
    s3_config = bcm.S3OutputConfigurations(
        Compression="GZIP",
        Format="PARQUET",
        OutputType="S3",
        Overwrite="CREATE_NEW_REPORT"
    )
    
    s3_dest = bcm.S3Destination(
        S3Bucket="bucket",
        S3OutputConfigurations=s3_config,
        S3Prefix="prefix",
        S3Region="us-east-1"
    )
    
    dest_config = bcm.DestinationConfigurations(S3Destination=s3_dest)
    
    export_prop = bcm.ExportProperty(
        DataQuery=data_query,
        DestinationConfigurations=dest_config,
        Name=name,
        RefreshCadence=refresh
    )
    
    # Convert to dict then to JSON
    dict_repr = export_prop.to_dict()
    json_str = json.dumps(dict_repr)
    
    # Parse back from JSON
    parsed = json.loads(json_str)
    
    # Verify structure is preserved
    assert parsed["Name"] == name
    assert parsed["RefreshCadence"]["Frequency"] == frequency
    assert parsed["DataQuery"]["QueryStatement"] == "SELECT * FROM table"