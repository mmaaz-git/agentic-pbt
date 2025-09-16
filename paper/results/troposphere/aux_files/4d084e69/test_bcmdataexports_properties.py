import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.bcmdataexports as bcm
import pytest


@st.composite
def valid_string_strategy(draw):
    """Generate valid non-empty strings for AWS properties"""
    return draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip() != ""))


@st.composite
def s3_output_configurations_strategy(draw):
    """Generate valid S3OutputConfigurations"""
    compression = draw(st.sampled_from(["GZIP", "PARQUET"]))
    format_type = draw(st.sampled_from(["TEXT_OR_CSV", "PARQUET"]))
    output_type = draw(st.sampled_from(["S3"]))
    overwrite = draw(st.sampled_from(["CREATE_NEW_REPORT", "OVERWRITE_REPORT"]))
    
    return bcm.S3OutputConfigurations(
        Compression=compression,
        Format=format_type,
        OutputType=output_type,
        Overwrite=overwrite
    )


@st.composite
def s3_destination_strategy(draw):
    """Generate valid S3Destination objects"""
    s3_bucket = draw(valid_string_strategy())
    s3_prefix = draw(valid_string_strategy())
    s3_region = draw(st.sampled_from(["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1"]))
    s3_output_config = draw(s3_output_configurations_strategy())
    
    return bcm.S3Destination(
        S3Bucket=s3_bucket,
        S3OutputConfigurations=s3_output_config,
        S3Prefix=s3_prefix,
        S3Region=s3_region
    )


@st.composite
def data_query_strategy(draw):
    """Generate valid DataQuery objects"""
    query = draw(valid_string_strategy())
    
    obj = bcm.DataQuery(QueryStatement=query)
    
    # Optionally add TableConfigurations
    if draw(st.booleans()):
        table_configs = draw(st.dictionaries(
            valid_string_strategy(),
            st.dictionaries(valid_string_strategy(), valid_string_strategy(), max_size=5),
            max_size=3
        ))
        obj.TableConfigurations = table_configs
    
    return obj


@st.composite
def resource_tag_strategy(draw):
    """Generate valid ResourceTag objects"""
    key = draw(valid_string_strategy())
    value = draw(valid_string_strategy())
    return bcm.ResourceTag(Key=key, Value=value)


# Test 1: Type validation property
@given(
    bucket=st.one_of(st.integers(), st.floats(), st.lists(st.text())),
    prefix=valid_string_strategy(),
    region=valid_string_strategy()
)
def test_type_validation_enforced(bucket, prefix, region):
    """Test that incorrect types are rejected as per __setattr__ validation"""
    assume(not isinstance(bucket, str))
    
    with pytest.raises(TypeError):
        # S3Bucket should be a string, not other types
        config = bcm.S3OutputConfigurations(
            Compression="GZIP",
            Format="PARQUET",
            OutputType="S3",
            Overwrite="CREATE_NEW_REPORT"
        )
        dest = bcm.S3Destination(
            S3Bucket=bucket,  # Wrong type - should raise TypeError
            S3OutputConfigurations=config,
            S3Prefix=prefix,
            S3Region=region
        )


# Test 2: Required property enforcement
@given(
    query=valid_string_strategy(),
    include_optional=st.booleans()
)
def test_required_properties_validated(query, include_optional):
    """Test that required properties must be provided during validation"""
    # DataQuery has QueryStatement as required, TableConfigurations as optional
    data_query = bcm.DataQuery(QueryStatement=query)
    
    if include_optional:
        data_query.TableConfigurations = {"test": {"key": "value"}}
    
    # Should be able to convert to dict without error if all required props present
    result = data_query.to_dict()
    assert "QueryStatement" in result
    assert result["QueryStatement"] == query
    
    if include_optional:
        assert "TableConfigurations" in result


# Test 3: Property get/set round-trip
@given(
    s3_dest=s3_destination_strategy(),
)
def test_property_get_set_roundtrip(s3_dest):
    """Test that properties can be set and retrieved with same value"""
    # Access properties and verify they match what was set
    assert s3_dest.S3Bucket == s3_dest.S3Bucket  # Should be idempotent
    assert s3_dest.S3Prefix == s3_dest.S3Prefix
    assert s3_dest.S3Region == s3_dest.S3Region
    
    # Verify nested objects work correctly
    assert isinstance(s3_dest.S3OutputConfigurations, bcm.S3OutputConfigurations)
    
    # Verify to_dict preserves structure
    dict_repr = s3_dest.to_dict()
    assert "S3Bucket" in dict_repr
    assert "S3Prefix" in dict_repr
    assert "S3Region" in dict_repr
    assert "S3OutputConfigurations" in dict_repr


# Test 4: to_dict() preserves all set properties
@given(
    data_query=data_query_strategy(),
)
def test_to_dict_preserves_properties(data_query):
    """Test that to_dict() correctly preserves all properties"""
    dict_repr = data_query.to_dict()
    
    # Required property should always be present
    assert "QueryStatement" in dict_repr
    assert dict_repr["QueryStatement"] == data_query.QueryStatement
    
    # Optional property should be present only if set
    if hasattr(data_query, "TableConfigurations"):
        assert "TableConfigurations" in dict_repr
        assert dict_repr["TableConfigurations"] == data_query.TableConfigurations
    else:
        # If not set, it shouldn't appear in dict
        assert "TableConfigurations" not in dict_repr or dict_repr.get("TableConfigurations") is None


# Test 5: Nested object validation
@given(
    dest_config_data=st.data()
)
def test_destination_configurations_nested_validation(dest_config_data):
    """Test that DestinationConfigurations properly validates nested S3Destination"""
    s3_dest = dest_config_data.draw(s3_destination_strategy())
    
    dest_config = bcm.DestinationConfigurations(S3Destination=s3_dest)
    
    # Should preserve the nested structure
    assert dest_config.S3Destination == s3_dest
    dict_repr = dest_config.to_dict()
    assert "S3Destination" in dict_repr
    
    # Nested dict should have the S3 destination properties
    s3_dest_dict = dict_repr["S3Destination"]
    assert "S3Bucket" in s3_dest_dict
    assert "S3Prefix" in s3_dest_dict


# Test 6: Export object with all components
@given(
    name=valid_string_strategy(),
    description=st.one_of(valid_string_strategy(), st.none()),
    tags=st.lists(resource_tag_strategy(), max_size=10)
)
@settings(max_examples=50)
def test_export_object_complete_validation(name, description, tags):
    """Test the main Export object with all its components"""
    # Build the nested structure
    data_query = bcm.DataQuery(QueryStatement="SELECT * FROM cost_table")
    
    s3_config = bcm.S3OutputConfigurations(
        Compression="GZIP",
        Format="PARQUET", 
        OutputType="S3",
        Overwrite="CREATE_NEW_REPORT"
    )
    
    s3_dest = bcm.S3Destination(
        S3Bucket="my-bucket",
        S3OutputConfigurations=s3_config,
        S3Prefix="exports/",
        S3Region="us-east-1"
    )
    
    dest_config = bcm.DestinationConfigurations(S3Destination=s3_dest)
    
    refresh = bcm.RefreshCadence(Frequency="SYNCHRONOUS")
    
    export_prop = bcm.ExportProperty(
        DataQuery=data_query,
        DestinationConfigurations=dest_config,
        Name=name,
        RefreshCadence=refresh
    )
    
    if description:
        export_prop.Description = description
    
    # Create the main Export object
    export_obj = bcm.Export(
        title="TestExport",
        Export=export_prop
    )
    
    if tags:
        export_obj.Tags = tags
    
    # Validate it can be serialized
    dict_repr = export_obj.to_dict()
    assert "Type" in dict_repr
    assert dict_repr["Type"] == "AWS::BCMDataExports::Export"
    assert "Properties" in dict_repr
    
    props = dict_repr["Properties"]
    assert "Export" in props
    
    # Check nested structure is preserved
    export_dict = props["Export"]
    assert "Name" in export_dict
    assert export_dict["Name"] == name
    
    if description:
        assert "Description" in export_dict
        assert export_dict["Description"] == description
    
    if tags:
        assert "Tags" in props
        assert len(props["Tags"]) == len(tags)