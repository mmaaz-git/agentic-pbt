import sys
import json
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.strategies import composite
import pytest

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import iotanalytics, AWSProperty, AWSObject, Tags, AWSHelperFn, Ref, GetAtt
from troposphere.validators import integer, double, boolean


class TestHelperFn(AWSHelperFn):
    """A test helper function to check validation bypass"""
    def __init__(self, data):
        self.data = data


@composite
def special_characters_text(draw):
    """Generate text with special characters that might break serialization"""
    return draw(st.one_of(
        st.just(''),  # Empty string
        st.just(' '),  # Single space
        st.just('\n'),  # Newline
        st.just('\t'),  # Tab
        st.just('\\'),  # Backslash
        st.just('"'),  # Quote
        st.just("'"),  # Single quote
        st.just('{"key": "value"}'),  # JSON-like string
        st.just('${variable}'),  # Template variable
        st.just('arn:aws:*:*:*:*'),  # Wildcard ARN
        st.text().filter(lambda x: any(c in x for c in ['\n', '\t', '"', '\\'])),
        st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1)
    ))


@given(
    name=special_characters_text(),
    type_str=special_characters_text()
)
def test_column_with_special_characters(name, type_str):
    """Test Column with special characters in strings"""
    
    assume(name and type_str)  # Skip empty strings for required fields
    
    column = iotanalytics.Column()
    column.Name = name
    column.Type = type_str
    
    # Should be able to serialize even with special characters
    serialized = column.to_dict(validation=False)
    assert serialized["Name"] == name
    assert serialized["Type"] == type_str
    
    # Should be able to convert to JSON
    json_str = column.to_json(validation=False)
    parsed = json.loads(json_str)
    assert parsed["Name"] == name
    assert parsed["Type"] == type_str
    
    # Round-trip through JSON
    reconstructed = iotanalytics.Column._from_dict(**parsed)
    assert reconstructed.Name == name
    assert reconstructed.Type == type_str


@given(
    title=st.text(min_size=1, max_size=100)
)
def test_invalid_resource_title_validation(title):
    """Test that resource titles are properly validated"""
    
    # Titles must be alphanumeric only
    try:
        channel = iotanalytics.Channel(title)
        
        # If it succeeded, title should be alphanumeric
        assert title.isalnum(), f"Non-alphanumeric title accepted: {title}"
        
        # Title should be preserved
        assert channel.title == title
    except ValueError as e:
        # Should only fail for non-alphanumeric titles
        assert not title.isalnum() or not title, f"Alphanumeric title rejected: {title}"
        assert "not alphanumeric" in str(e)


@given(
    value=st.one_of(
        st.lists(st.integers()),  # List of integers instead of single integer
        st.dictionaries(st.text(), st.integers()),  # Dict instead of integer
        st.just(None),  # None value
        st.just(float('inf')),  # Infinity
        st.just(float('nan')),  # NaN
        st.just(complex(1, 2))  # Complex number
    )
)
def test_integer_validator_with_invalid_types(value):
    """Test that integer validator properly rejects invalid types"""
    
    retention = iotanalytics.RetentionPeriod()
    
    # These should all fail validation
    with pytest.raises((ValueError, TypeError)):
        retention.NumberOfDays = value


@given(
    activities=st.lists(
        st.just(None),
        min_size=1,
        max_size=5
    )
)
def test_pipeline_with_null_activities(activities):
    """Test Pipeline with null/None activities"""
    
    pipeline = iotanalytics.Pipeline("TestPipeline")
    
    # Setting None activities should fail or be handled gracefully
    with pytest.raises((AttributeError, TypeError, ValueError)):
        pipeline.PipelineActivities = activities


def test_helper_fn_validation_bypass():
    """Test that AWSHelperFn values bypass normal validation"""
    
    retention = iotanalytics.RetentionPeriod()
    
    # Normal validation would reject a string for NumberOfDays
    with pytest.raises((ValueError, TypeError)):
        retention.NumberOfDays = "not_a_number"
    
    # But AWSHelperFn should bypass validation
    helper_value = TestHelperFn("dynamic_value")
    retention.NumberOfDays = helper_value
    
    # The helper function should be preserved
    assert retention.NumberOfDays == helper_value
    
    # Should serialize with the helper function
    serialized = retention.to_dict(validation=False)
    assert retention.NumberOfDays == helper_value


@given(
    max_versions=st.integers(min_value=-1000, max_value=1000),
    unlimited=st.booleans()
)
def test_versioning_configuration_mutual_exclusion(max_versions, unlimited):
    """Test VersioningConfiguration with potentially conflicting settings"""
    
    config = iotanalytics.VersioningConfiguration()
    
    # Set both properties
    config.MaxVersions = max_versions
    config.Unlimited = unlimited
    
    # Both should be preserved (no mutual exclusion validation)
    assert config.MaxVersions == max_versions
    assert config.Unlimited == unlimited
    
    # Serialize and check both are present
    serialized = config.to_dict(validation=False)
    assert serialized["MaxVersions"] == max_versions
    assert serialized["Unlimited"] == unlimited


@given(
    bucket=st.text(min_size=1, max_size=200),
    key_prefix=st.text(min_size=0, max_size=200),
    role_arn=st.text(min_size=1, max_size=200)
)
def test_customer_managed_s3_validation_with_validation_flag(bucket, key_prefix, role_arn):
    """Test CustomerManagedS3 with validation enabled"""
    
    obj = iotanalytics.CustomerManagedS3()
    obj.Bucket = bucket
    obj.RoleArn = role_arn
    if key_prefix:
        obj.KeyPrefix = key_prefix
    
    # With validation=True, should validate required properties
    try:
        serialized = obj.to_dict(validation=True)
        # If it succeeded, all required properties should be present
        assert "Bucket" in serialized
        assert "RoleArn" in serialized
    except ValueError as e:
        # Should only fail if required properties are missing
        # But we set them, so this shouldn't happen
        pytest.fail(f"Validation failed unexpectedly: {e}")


@given(
    datastore_name=st.one_of(
        st.none(),
        st.just(""),
        st.text(min_size=1, max_size=100)
    )
)
def test_datastore_optional_name_property(datastore_name):
    """Test Datastore with optional DatastoreName property"""
    
    datastore = iotanalytics.Datastore("TestDatastore")
    
    if datastore_name is not None:
        datastore.DatastoreName = datastore_name
    
    # Should serialize without error
    serialized = datastore.to_dict(validation=False)
    
    if datastore_name:
        assert serialized["Properties"]["DatastoreName"] == datastore_name
    elif datastore_name == "":
        # Empty string might be preserved or omitted
        if "DatastoreName" in serialized["Properties"]:
            assert serialized["Properties"]["DatastoreName"] == ""
    else:
        # None should not be in the serialized output
        assert "DatastoreName" not in serialized.get("Properties", {})


@given(
    storage_types=st.lists(
        st.sampled_from(["CustomerManagedS3", "ServiceManagedS3", "IotSiteWiseMultiLayerStorage"]),
        min_size=1,
        max_size=3,
        unique=True
    )
)
def test_datastore_storage_multiple_types(storage_types):
    """Test DatastoreStorage with multiple storage types set"""
    
    storage = iotanalytics.DatastoreStorage()
    
    for storage_type in storage_types:
        if storage_type == "CustomerManagedS3":
            cms3 = iotanalytics.CustomerManagedS3()
            cms3.Bucket = "test-bucket"
            cms3.RoleArn = "arn:aws:iam::123456789012:role/TestRole"
            storage.CustomerManagedS3 = cms3
        elif storage_type == "ServiceManagedS3":
            storage.ServiceManagedS3 = {}
        elif storage_type == "IotSiteWiseMultiLayerStorage":
            iotsw = iotanalytics.IotSiteWiseMultiLayerStorage()
            storage.IotSiteWiseMultiLayerStorage = iotsw
    
    # All storage types should be preserved (no mutual exclusion)
    serialized = storage.to_dict(validation=False)
    
    for storage_type in storage_types:
        assert storage_type in serialized


@given(
    json_config=st.one_of(
        st.none(),
        st.just({}),
        st.dictionaries(st.text(min_size=1, max_size=20), st.text())
    ),
    parquet_config_present=st.booleans()
)
def test_file_format_configuration_both_formats(json_config, parquet_config_present):
    """Test FileFormatConfiguration with both JSON and Parquet configs"""
    
    file_format = iotanalytics.FileFormatConfiguration()
    
    if json_config is not None:
        file_format.JsonConfiguration = json_config
    
    if parquet_config_present:
        parquet = iotanalytics.ParquetConfiguration()
        file_format.ParquetConfiguration = parquet
    
    # Both should be allowed simultaneously
    serialized = file_format.to_dict(validation=False)
    
    if json_config is not None:
        assert "JsonConfiguration" in serialized
        assert serialized["JsonConfiguration"] == json_config
    
    if parquet_config_present:
        assert "ParquetConfiguration" in serialized


@given(
    filter_expr=special_characters_text()
)
def test_filter_activity_with_complex_expressions(filter_expr):
    """Test Filter activity with complex filter expressions"""
    
    assume(filter_expr)  # Skip empty string
    
    filter_activity = iotanalytics.Filter()
    filter_activity.Filter = filter_expr
    filter_activity.Name = "TestFilter"
    
    # Expression should be preserved as-is
    assert filter_activity.Filter == filter_expr
    
    # Should serialize
    serialized = filter_activity.to_dict(validation=False)
    assert serialized["Filter"] == filter_expr
    assert serialized["Name"] == "TestFilter"


@given(
    math_expr=st.text(min_size=1, max_size=500),
    attribute=st.text(min_size=1, max_size=100)
)
def test_math_activity_expression_validation(math_expr, attribute):
    """Test Math activity with various expressions"""
    
    math_activity = iotanalytics.Math()
    math_activity.Math = math_expr
    math_activity.Attribute = attribute
    math_activity.Name = "TestMath"
    
    # Expressions should be preserved
    assert math_activity.Math == math_expr
    assert math_activity.Attribute == attribute
    
    # Serialize
    serialized = math_activity.to_dict(validation=False)
    assert serialized["Math"] == math_expr
    assert serialized["Attribute"] == attribute


@given(
    tags=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=50),
            st.text(min_size=0, max_size=200)
        ),
        min_size=0,
        max_size=50
    )
)
def test_tags_property_validation(tags):
    """Test Tags property on resources"""
    
    channel = iotanalytics.Channel("TestChannel")
    
    # Create Tags object
    tags_obj = Tags()
    for key, value in tags:
        tags_obj.tags.append({"Key": key, "Value": value})
    
    channel.Tags = tags_obj
    
    # Tags should be preserved
    assert channel.Tags == tags_obj
    
    # Serialize
    serialized = channel.to_dict(validation=False)
    
    if tags:
        assert "Tags" in serialized
        # Tags might be in Properties
        if "Properties" in serialized:
            if "Tags" in serialized["Properties"]:
                assert len(serialized["Properties"]["Tags"]) == len(tags)


@given(
    sql_query=special_characters_text()
)
def test_query_action_sql_injection_characters(sql_query):
    """Test QueryAction with SQL injection-like patterns"""
    
    assume(sql_query)  # Skip empty
    
    query_action = iotanalytics.QueryAction()
    query_action.SqlQuery = sql_query
    
    # SQL should be preserved as-is (validation is AWS's responsibility)
    assert query_action.SqlQuery == sql_query
    
    # Should serialize
    serialized = query_action.to_dict(validation=False)
    assert serialized["SqlQuery"] == sql_query


@given(
    entry_name=st.one_of(
        st.none(),
        st.just(""),
        special_characters_text()
    )
)
def test_dataset_content_delivery_rule_optional_entry_name(entry_name):
    """Test DatasetContentDeliveryRule with optional EntryName"""
    
    rule = iotanalytics.DatasetContentDeliveryRule()
    
    # Set required Destination
    dest = iotanalytics.DatasetContentDeliveryRuleDestination()
    s3_dest = iotanalytics.S3DestinationConfiguration()
    s3_dest.Bucket = "test-bucket"
    s3_dest.Key = "test-key"
    s3_dest.RoleArn = "arn:aws:iam::123456789012:role/TestRole"
    dest.S3DestinationConfiguration = s3_dest
    rule.Destination = dest
    
    if entry_name is not None:
        rule.EntryName = entry_name
    
    # Should serialize
    serialized = rule.to_dict(validation=False)
    assert "Destination" in serialized
    
    if entry_name:
        assert serialized["EntryName"] == entry_name
    elif entry_name == "":
        if "EntryName" in serialized:
            assert serialized["EntryName"] == ""
    else:
        assert "EntryName" not in serialized


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])