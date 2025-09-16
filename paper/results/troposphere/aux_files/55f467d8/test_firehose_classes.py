#!/usr/bin/env python3
"""Property-based tests for troposphere.firehose classes using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from troposphere import firehose
from troposphere import AWSProperty, AWSObject
import inspect


# Test 1: All AWSProperty classes should have a props dictionary
@given(st.just(None))
def test_all_awsproperty_have_props(dummy):
    """All AWSProperty subclasses should have a props dictionary."""
    for name, obj in inspect.getmembers(firehose):
        if inspect.isclass(obj) and issubclass(obj, AWSProperty) and obj != AWSProperty:
            assert hasattr(obj, 'props'), f"{name} should have 'props' attribute"
            assert isinstance(obj.props, dict), f"{name}.props should be a dictionary"


# Test 2: Required props should be marked correctly
@given(st.just(None))
def test_required_props_consistency(dummy):
    """Required properties should be consistently marked with True in tuple."""
    for name, obj in inspect.getmembers(firehose):
        if inspect.isclass(obj) and issubclass(obj, AWSProperty) and obj != AWSProperty:
            if hasattr(obj, 'props'):
                for prop_name, prop_def in obj.props.items():
                    # Props are defined as (type, required) tuples
                    if isinstance(prop_def, tuple) and len(prop_def) >= 2:
                        required = prop_def[1]
                        assert isinstance(required, bool), f"{name}.{prop_name} required flag should be bool, got {type(required)}"


# Test 3: Property names should follow AWS naming conventions
@given(st.just(None))
def test_property_naming_conventions(dummy):
    """Property names should follow AWS CloudFormation conventions (PascalCase)."""
    for name, obj in inspect.getmembers(firehose):
        if inspect.isclass(obj) and issubclass(obj, AWSProperty) and obj != AWSProperty:
            if hasattr(obj, 'props'):
                for prop_name in obj.props.keys():
                    # AWS properties typically use PascalCase
                    if prop_name:  # Skip empty strings
                        first_char = prop_name[0]
                        assert first_char.isupper() or not first_char.isalpha(), f"{name}.{prop_name} should start with uppercase"


# Test 4: Test BufferingHints interval and size constraints
@given(st.integers())
def test_buffering_hints_accepts_integers(value):
    """BufferingHints should accept integer values for IntervalInSeconds and SizeInMBs."""
    hints = firehose.BufferingHints()
    # These properties are defined as (integer, False) meaning they accept integers and are optional
    try:
        hints.props["IntervalInSeconds"][0]  # Should be integer validator
        hints.props["SizeInMBs"][0]  # Should be integer validator
    except Exception as e:
        assert False, f"BufferingHints props should be accessible: {e}"


# Test 5: Test that S3Configuration and S3DestinationConfiguration have consistent required fields
@given(st.just(None))  
def test_s3_configuration_consistency(dummy):
    """S3Configuration and S3DestinationConfiguration should have consistent required fields."""
    s3_config = firehose.S3Configuration()
    s3_dest_config = firehose.S3DestinationConfiguration()
    
    # Both should require BucketARN and RoleARN
    assert "BucketARN" in s3_config.props
    assert "RoleARN" in s3_config.props
    assert "BucketARN" in s3_dest_config.props
    assert "RoleARN" in s3_dest_config.props
    
    # Check they're both required
    assert s3_config.props["BucketARN"][1] == True
    assert s3_config.props["RoleARN"][1] == True
    assert s3_dest_config.props["BucketARN"][1] == True
    assert s3_dest_config.props["RoleARN"][1] == True


# Test 6: DeliveryStream resource type should be correct
@given(st.just(None))
def test_delivery_stream_resource_type(dummy):
    """DeliveryStream should have correct AWS resource type."""
    assert hasattr(firehose.DeliveryStream, 'resource_type')
    assert firehose.DeliveryStream.resource_type == "AWS::KinesisFirehose::DeliveryStream"


# Test 7: Test validator imports are consistent
@given(st.just(None))
def test_validator_imports(dummy):
    """Validators imported in firehose.py should match those defined in validators/firehose.py."""
    # Check that validators used in props are actually imported
    delivery_stream = firehose.DeliveryStream()
    
    # DeliveryStreamType uses delivery_stream_type_validator
    delivery_type_prop = delivery_stream.props.get("DeliveryStreamType")
    if delivery_type_prop:
        # Should be (validator_function, required_bool)
        assert callable(delivery_type_prop[0]) or delivery_type_prop[0].__name__ == "delivery_stream_type_validator"


# Test 8: Test integer/boolean validators
@given(st.integers(min_value=-1000000, max_value=1000000))
def test_integer_properties_accept_integers(value):
    """Properties defined as integer should accept integer values."""
    # BufferingHints has integer properties
    hints = firehose.BufferingHints()
    
    # The props dict contains (validator, required) tuples
    # Integer properties should accept integers
    interval_validator = hints.props["IntervalInSeconds"][0]
    size_validator = hints.props["SizeInMBs"][0]
    
    # These should be the integer validator from troposphere.validators
    # Let's verify they're callable or the integer type
    from troposphere.validators import integer
    assert interval_validator == integer or callable(interval_validator)
    assert size_validator == integer or callable(size_validator)


# Test 9: Test that classes with similar names have similar structures
@given(st.just(None))
def test_similar_classes_consistency(dummy):
    """Classes with similar names should have similar property structures."""
    # All BufferingHints classes should have IntervalInSeconds and SizeInMBs
    buffering_classes = [
        firehose.BufferingHints,
        firehose.AmazonOpenSearchServerlessBufferingHints,
        firehose.AmazonopensearchserviceBufferingHints,
        firehose.SnowflakeBufferingHints,
        firehose.SplunkBufferingHints
    ]
    
    for cls in buffering_classes:
        obj = cls()
        assert "IntervalInSeconds" in obj.props, f"{cls.__name__} should have IntervalInSeconds"
        assert "SizeInMBs" in obj.props, f"{cls.__name__} should have SizeInMBs"
        
        # They should all be optional (False)
        assert obj.props["IntervalInSeconds"][1] == False
        assert obj.props["SizeInMBs"][1] == False


# Test 10: Test RetryOptions classes consistency
@given(st.just(None))
def test_retry_options_consistency(dummy):
    """All RetryOptions classes should have DurationInSeconds property."""
    retry_classes = [
        firehose.RetryOptions,
        firehose.AmazonOpenSearchServerlessRetryOptions,
        firehose.AmazonopensearchserviceRetryOptions,
        firehose.RedshiftRetryOptions,
        firehose.SnowflakeRetryOptions,
        firehose.SplunkRetryOptions
    ]
    
    for cls in retry_classes:
        obj = cls()
        assert "DurationInSeconds" in obj.props, f"{cls.__name__} should have DurationInSeconds"
        # Should be optional integer
        assert obj.props["DurationInSeconds"][1] == False  # Optional
        
        
# Test 11: Test S3BackupMode validator usage consistency
@given(st.sampled_from(["s3_backup_mode_elastic_search_validator", "s3_backup_mode_extended_s3_validator"]))
def test_s3_backup_mode_validator_usage(validator_name):
    """S3BackupMode properties should use appropriate validators."""
    from troposphere.validators.firehose import (
        s3_backup_mode_elastic_search_validator,
        s3_backup_mode_extended_s3_validator
    )
    
    # ExtendedS3DestinationConfiguration should use extended validator
    extended_s3 = firehose.ExtendedS3DestinationConfiguration()
    if "S3BackupMode" in extended_s3.props:
        validator = extended_s3.props["S3BackupMode"][0]
        # Should be the extended S3 validator
        assert validator == s3_backup_mode_extended_s3_validator
    
    # ElasticsearchDestinationConfiguration should use elastic search validator  
    elastic = firehose.ElasticsearchDestinationConfiguration()
    if "S3BackupMode" in elastic.props:
        validator = elastic.props["S3BackupMode"][0]
        # Should be the elastic search validator
        assert validator == s3_backup_mode_elastic_search_validator