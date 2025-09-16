import sys
import json
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import pytest

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import iotanalytics, AWSProperty, AWSObject, Tags
from troposphere.validators import integer, double, boolean


@composite
def valid_cloudformation_name(draw):
    """Generate valid CloudFormation resource names (alphanumeric only)"""
    return draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=100))


@composite
def valid_string_property(draw):
    """Generate valid string properties"""
    return draw(st.text(min_size=1, max_size=500).filter(lambda x: not x.isspace()))


@composite
def valid_s3_bucket_name(draw):
    """Generate valid S3 bucket names"""
    return draw(st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-'), 
                        min_size=3, max_size=63).filter(lambda x: not x.startswith('-') and not x.endswith('-')))


@composite
def valid_arn(draw):
    """Generate valid AWS ARN strings"""
    service = draw(st.sampled_from(['iam', 's3', 'iot', 'lambda']))
    resource = draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=50))
    return f"arn:aws:{service}:us-east-1:123456789012:{resource}"


@composite
def valid_integer_property(draw):
    """Generate valid integer values for properties"""
    return draw(st.integers(min_value=0, max_value=2147483647))


@composite
def valid_double_property(draw):
    """Generate valid double values for properties"""
    return draw(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))


@composite
def valid_boolean_property(draw):
    """Generate valid boolean values"""
    return draw(st.booleans())


@given(
    bucket=valid_s3_bucket_name(),
    key_prefix=st.one_of(st.none(), valid_string_property()),
    role_arn=valid_arn()
)
def test_customer_managed_s3_round_trip(bucket, key_prefix, role_arn):
    """Test that CustomerManagedS3 can be serialized and deserialized without data loss"""
    
    # Create instance with properties
    original = iotanalytics.CustomerManagedS3()
    original.Bucket = bucket
    original.RoleArn = role_arn
    if key_prefix is not None:
        original.KeyPrefix = key_prefix
    
    # Serialize to dict
    serialized = original.to_dict(validation=False)
    
    # Deserialize back
    reconstructed = iotanalytics.CustomerManagedS3._from_dict(**serialized)
    
    # Check that all properties are preserved
    assert reconstructed.Bucket == original.Bucket
    assert reconstructed.RoleArn == original.RoleArn
    if key_prefix is not None:
        assert reconstructed.KeyPrefix == original.KeyPrefix


@given(
    number_of_days=st.one_of(st.none(), valid_integer_property()),
    unlimited=st.one_of(st.none(), valid_boolean_property())
)
def test_retention_period_validation(number_of_days, unlimited):
    """Test RetentionPeriod property validation"""
    
    retention = iotanalytics.RetentionPeriod()
    
    # Test setting NumberOfDays with integer validator
    if number_of_days is not None:
        retention.NumberOfDays = number_of_days
        # The integer validator should accept it and preserve the value
        assert retention.NumberOfDays == number_of_days
    
    # Test setting Unlimited with boolean validator
    if unlimited is not None:
        retention.Unlimited = unlimited
        # The boolean validator should accept it and preserve the value
        assert retention.Unlimited == unlimited


@given(
    channel_name=st.one_of(st.none(), valid_cloudformation_name()),
    service_managed=st.one_of(st.none(), st.booleans())
)
def test_channel_resource_type(channel_name, service_managed):
    """Test that Channel resource has correct resource type"""
    
    # Create Channel with optional properties
    if channel_name:
        channel = iotanalytics.Channel("TestChannel")
        channel.ChannelName = channel_name
    else:
        channel = iotanalytics.Channel("TestChannel")
    
    if service_managed is not None:
        channel_storage = iotanalytics.ChannelStorage()
        channel_storage.ServiceManagedS3 = {}
        channel.ChannelStorage = channel_storage
    
    # Check resource type is correctly set
    assert channel.resource_type == "AWS::IoTAnalytics::Channel"
    
    # Serialize and check Type field
    serialized = channel.to_dict(validation=False)
    assert serialized.get("Type") == "AWS::IoTAnalytics::Channel"


@given(
    compute_type=valid_string_property(),
    volume_size=valid_integer_property()
)
def test_resource_configuration_required_properties(compute_type, volume_size):
    """Test that ResourceConfiguration validates required properties"""
    
    # Create ResourceConfiguration with required properties
    config = iotanalytics.ResourceConfiguration()
    config.ComputeType = compute_type
    config.VolumeSizeInGB = volume_size
    
    # Should serialize without errors when all required props are set
    serialized = config.to_dict(validation=False)
    assert "ComputeType" in serialized
    assert "VolumeSizeInGB" in serialized
    assert serialized["ComputeType"] == compute_type
    assert serialized["VolumeSizeInGB"] == volume_size


@given(
    variable_name=valid_cloudformation_name(),
    double_value=st.one_of(st.none(), valid_double_property()),
    string_value=st.one_of(st.none(), valid_string_property())
)
def test_variable_type_validation(variable_name, double_value, string_value):
    """Test that Variable correctly validates double and string types"""
    
    var = iotanalytics.Variable()
    var.VariableName = variable_name
    
    # Test double validator
    if double_value is not None:
        var.DoubleValue = double_value
        assert var.DoubleValue == double_value
    
    # Test string property
    if string_value is not None:
        var.StringValue = string_value
        assert var.StringValue == string_value
    
    # Serialize and verify
    serialized = var.to_dict(validation=False)
    assert serialized["VariableName"] == variable_name
    if double_value is not None:
        assert serialized["DoubleValue"] == double_value
    if string_value is not None:
        assert serialized["StringValue"] == string_value


@given(
    name=valid_cloudformation_name(),
    type_str=valid_string_property()
)
def test_column_round_trip(name, type_str):
    """Test Column serialization round-trip"""
    
    # Create Column
    column = iotanalytics.Column()
    column.Name = name
    column.Type = type_str
    
    # Serialize
    serialized = column.to_dict(validation=False)
    
    # Deserialize
    reconstructed = iotanalytics.Column._from_dict(**serialized)
    
    # Verify round-trip preservation
    assert reconstructed.Name == name
    assert reconstructed.Type == type_str


@given(
    attributes=st.lists(valid_string_property(), min_size=1, max_size=10)
)
def test_remove_attributes_list_property(attributes):
    """Test that RemoveAttributes correctly handles list properties"""
    
    remove_attrs = iotanalytics.RemoveAttributes()
    remove_attrs.Name = "RemoveTest"
    remove_attrs.Attributes = attributes
    
    # Verify list is preserved
    assert remove_attrs.Attributes == attributes
    
    # Serialize and check
    serialized = remove_attrs.to_dict(validation=False)
    assert serialized["Attributes"] == attributes
    assert serialized["Name"] == "RemoveTest"


@given(
    dataset_name=valid_cloudformation_name(),
    actions=st.lists(
        st.builds(
            lambda name: {"ActionName": name, "QueryAction": {"SqlQuery": "SELECT * FROM data"}},
            valid_cloudformation_name()
        ),
        min_size=1,
        max_size=3
    )
)
def test_dataset_complex_structure(dataset_name, actions):
    """Test Dataset with complex nested structures"""
    
    dataset = iotanalytics.Dataset("TestDataset")
    dataset.DatasetName = dataset_name
    
    # Build Action objects
    action_objs = []
    for action_dict in actions:
        action = iotanalytics.Action()
        action.ActionName = action_dict["ActionName"]
        
        query_action = iotanalytics.QueryAction()
        query_action.SqlQuery = action_dict["QueryAction"]["SqlQuery"]
        action.QueryAction = query_action
        
        action_objs.append(action)
    
    dataset.Actions = action_objs
    
    # Verify resource type
    assert dataset.resource_type == "AWS::IoTAnalytics::Dataset"
    
    # Serialize and check structure
    serialized = dataset.to_dict(validation=False)
    assert serialized["Type"] == "AWS::IoTAnalytics::Dataset"
    assert "Properties" in serialized
    assert "Actions" in serialized["Properties"]
    assert len(serialized["Properties"]["Actions"]) == len(actions)


@given(
    partition_name=valid_string_property(),
    timestamp_format=st.one_of(st.none(), valid_string_property())
)
def test_timestamp_partition_optional_property(partition_name, timestamp_format):
    """Test TimestampPartition with optional property"""
    
    partition = iotanalytics.TimestampPartition()
    partition.AttributeName = partition_name
    
    if timestamp_format is not None:
        partition.TimestampFormat = timestamp_format
    
    # Serialize
    serialized = partition.to_dict(validation=False)
    assert serialized["AttributeName"] == partition_name
    
    if timestamp_format is not None:
        assert serialized["TimestampFormat"] == timestamp_format
    else:
        assert "TimestampFormat" not in serialized


@given(
    batch_size=valid_integer_property(),
    lambda_name=valid_string_property(),
    activity_name=valid_cloudformation_name()
)
def test_lambda_activity_integer_validation(batch_size, lambda_name, activity_name):
    """Test Lambda activity with integer validation"""
    
    lambda_activity = iotanalytics.Lambda()
    lambda_activity.BatchSize = batch_size
    lambda_activity.LambdaName = lambda_name
    lambda_activity.Name = activity_name
    
    # Integer should be validated and preserved
    assert lambda_activity.BatchSize == batch_size
    
    # Serialize and verify
    serialized = lambda_activity.to_dict(validation=False)
    assert serialized["BatchSize"] == batch_size
    assert serialized["LambdaName"] == lambda_name
    assert serialized["Name"] == activity_name


@given(
    max_versions=st.one_of(st.none(), valid_integer_property()),
    unlimited=st.one_of(st.none(), valid_boolean_property())
)
def test_versioning_configuration_validators(max_versions, unlimited):
    """Test VersioningConfiguration with integer and boolean validators"""
    
    config = iotanalytics.VersioningConfiguration()
    
    if max_versions is not None:
        config.MaxVersions = max_versions
        assert config.MaxVersions == max_versions
    
    if unlimited is not None:
        config.Unlimited = unlimited
        assert config.Unlimited == unlimited
    
    # Serialize
    serialized = config.to_dict(validation=False)
    
    if max_versions is not None:
        assert serialized["MaxVersions"] == max_versions
    if unlimited is not None:
        assert serialized["Unlimited"] == unlimited


@given(
    datastore_name=valid_cloudformation_name(),
    json_config=st.one_of(st.none(), st.just({})),
    bucket=st.one_of(st.none(), valid_s3_bucket_name())
)
def test_datastore_file_format_configuration(datastore_name, json_config, bucket):
    """Test Datastore with FileFormatConfiguration"""
    
    datastore = iotanalytics.Datastore("TestDatastore")
    datastore.DatastoreName = datastore_name
    
    if json_config is not None or bucket is not None:
        file_format = iotanalytics.FileFormatConfiguration()
        
        if json_config is not None:
            file_format.JsonConfiguration = json_config
        
        if bucket is not None:
            parquet_config = iotanalytics.ParquetConfiguration()
            schema_def = iotanalytics.SchemaDefinition()
            
            column = iotanalytics.Column()
            column.Name = "testColumn"
            column.Type = "STRING"
            schema_def.Columns = [column]
            
            parquet_config.SchemaDefinition = schema_def
            file_format.ParquetConfiguration = parquet_config
        
        datastore.FileFormatConfiguration = file_format
    
    # Verify resource type
    assert datastore.resource_type == "AWS::IoTAnalytics::Datastore"
    
    # Serialize without validation errors
    serialized = datastore.to_dict(validation=False)
    assert serialized["Type"] == "AWS::IoTAnalytics::Datastore"


if __name__ == "__main__":
    # Run all tests with pytest
    pytest.main([__file__, "-v"])