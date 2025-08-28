#!/usr/bin/env python3
"""Property-based tests for troposphere.lookoutequipment module."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import troposphere.lookoutequipment as le
import json
import pytest


# Strategy for valid CloudFormation resource titles (alphanumeric only)
valid_titles = st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50)

# Strategy for S3 bucket names (simplified - actual rules are more complex)
bucket_names = st.text(alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="-"), min_size=3, max_size=63)

# Strategy for S3 prefixes
s3_prefixes = st.text(alphabet=st.characters(blacklist_characters="\x00"), max_size=1024)

# Strategy for ARNs
arns = st.text(min_size=1).map(lambda s: f"arn:aws:iam::123456789012:role/{s}")

# Strategy for KMS key IDs
kms_keys = st.text(min_size=1).map(lambda s: f"arn:aws:kms:us-east-1:123456789012:key/{s}")


@given(
    title=valid_titles,
    bucket=bucket_names,
    prefix=s3_prefixes,
)
def test_s3_input_configuration_round_trip(title, bucket, prefix):
    """Test that S3InputConfiguration can be created, serialized, and deserialized."""
    # Create the object
    config = le.S3InputConfiguration(
        title=title,
        Bucket=bucket,
        Prefix=prefix
    )
    
    # Convert to dict
    config_dict = config.to_dict()
    
    # Verify the dict has the expected structure
    assert "Bucket" in config_dict
    assert config_dict["Bucket"] == bucket
    if prefix:  # Prefix is optional
        assert "Prefix" in config_dict
        assert config_dict["Prefix"] == prefix
    
    # Create a new object from the dict
    new_config = le.S3InputConfiguration.from_dict(title, config_dict)
    
    # Verify they're equal
    assert config == new_config
    assert config.to_dict() == new_config.to_dict()


@given(
    title=valid_titles,
    bucket=bucket_names,
    prefix=s3_prefixes,
)
def test_s3_output_configuration_round_trip(title, bucket, prefix):
    """Test that S3OutputConfiguration can be created, serialized, and deserialized."""
    config = le.S3OutputConfiguration(
        title=title,
        Bucket=bucket,
        Prefix=prefix
    )
    
    config_dict = config.to_dict()
    
    assert "Bucket" in config_dict
    assert config_dict["Bucket"] == bucket
    if prefix:
        assert "Prefix" in config_dict
        assert config_dict["Prefix"] == prefix
    
    new_config = le.S3OutputConfiguration.from_dict(title, config_dict)
    
    assert config == new_config
    assert config.to_dict() == new_config.to_dict()


@given(
    title=valid_titles,
    data_delay=st.one_of(st.none(), st.integers(min_value=0, max_value=86400)),
    data_frequency=st.sampled_from(["PT1M", "PT5M", "PT10M", "PT15M", "PT30M", "PT1H"]),
    scheduler_name=st.one_of(st.none(), valid_titles),
    model_name=valid_titles,
    role_arn=arns,
    bucket_in=bucket_names,
    bucket_out=bucket_names,
)
def test_inference_scheduler_required_properties(
    title, data_delay, data_frequency, scheduler_name, model_name, role_arn, bucket_in, bucket_out
):
    """Test that InferenceScheduler correctly validates required properties."""
    # Create input/output configs
    input_config = le.DataInputConfiguration(
        S3InputConfiguration=le.S3InputConfiguration(Bucket=bucket_in)
    )
    output_config = le.DataOutputConfiguration(
        S3OutputConfiguration=le.S3OutputConfiguration(Bucket=bucket_out)
    )
    
    # Create scheduler with all required properties
    scheduler = le.InferenceScheduler(
        title,
        DataInputConfiguration=input_config,
        DataOutputConfiguration=output_config,
        DataUploadFrequency=data_frequency,
        ModelName=model_name,
        RoleArn=role_arn
    )
    
    # Add optional properties
    if data_delay is not None:
        scheduler.DataDelayOffsetInMinutes = data_delay
    if scheduler_name is not None:
        scheduler.InferenceSchedulerName = scheduler_name
    
    # Should not raise when converting to dict
    scheduler_dict = scheduler.to_dict()
    
    # Verify required properties are present
    props = scheduler_dict.get("Properties", {})
    assert "DataInputConfiguration" in props
    assert "DataOutputConfiguration" in props
    assert "DataUploadFrequency" in props
    assert props["DataUploadFrequency"] == data_frequency
    assert "ModelName" in props
    assert props["ModelName"] == model_name
    assert "RoleArn" in props
    assert props["RoleArn"] == role_arn


@given(
    invalid_title=st.text(alphabet=st.characters(whitelist_categories=("P", "S")), min_size=1)
)
def test_title_validation_rejects_non_alphanumeric(invalid_title):
    """Test that titles with non-alphanumeric characters are rejected."""
    assume(not invalid_title.isalnum())  # Only test non-alphanumeric titles
    
    with pytest.raises(ValueError, match="not alphanumeric"):
        le.InferenceScheduler(
            invalid_title,
            DataInputConfiguration=le.DataInputConfiguration(
                S3InputConfiguration=le.S3InputConfiguration(Bucket="test-bucket")
            ),
            DataOutputConfiguration=le.DataOutputConfiguration(
                S3OutputConfiguration=le.S3OutputConfiguration(Bucket="test-bucket")
            ),
            DataUploadFrequency="PT1H",
            ModelName="test-model",
            RoleArn="arn:aws:iam::123456789012:role/test"
        )


@given(
    title=valid_titles,
    invalid_delay=st.one_of(
        st.text(),  # strings that aren't integers
        st.floats(allow_nan=True, allow_infinity=True),  # floats including special values
        st.lists(st.integers()),  # lists
        st.dictionaries(st.text(), st.integers()),  # dicts
    )
)
def test_integer_validator_on_data_delay(title, invalid_delay):
    """Test that DataDelayOffsetInMinutes correctly validates integer inputs."""
    # Filter out values that could be valid integers
    try:
        int(invalid_delay)
        assume(False)  # Skip if it's actually convertible to int
    except (ValueError, TypeError):
        pass  # This is what we want to test
    
    scheduler = le.InferenceScheduler(
        title,
        DataInputConfiguration=le.DataInputConfiguration(
            S3InputConfiguration=le.S3InputConfiguration(Bucket="test-bucket")
        ),
        DataOutputConfiguration=le.DataOutputConfiguration(
            S3OutputConfiguration=le.S3OutputConfiguration(Bucket="test-bucket")
        ),
        DataUploadFrequency="PT1H",
        ModelName="test-model",
        RoleArn="arn:aws:iam::123456789012:role/test"
    )
    
    # Setting an invalid integer should raise
    with pytest.raises((ValueError, TypeError)):
        scheduler.DataDelayOffsetInMinutes = invalid_delay
        scheduler.to_dict()  # Force validation


@given(
    title=valid_titles,
    comp_delimiter=st.one_of(st.none(), st.text(max_size=10)),
    timestamp_fmt=st.one_of(st.none(), st.text(max_size=50)),
)
def test_input_name_configuration_optional_properties(title, comp_delimiter, timestamp_fmt):
    """Test that InputNameConfiguration handles optional properties correctly."""
    kwargs = {}
    if comp_delimiter is not None:
        kwargs["ComponentTimestampDelimiter"] = comp_delimiter
    if timestamp_fmt is not None:
        kwargs["TimestampFormat"] = timestamp_fmt
    
    config = le.InputNameConfiguration(title=title, **kwargs)
    config_dict = config.to_dict()
    
    # Optional properties should only appear if set
    if comp_delimiter is not None:
        assert "ComponentTimestampDelimiter" in config_dict
        assert config_dict["ComponentTimestampDelimiter"] == comp_delimiter
    else:
        assert "ComponentTimestampDelimiter" not in config_dict
        
    if timestamp_fmt is not None:
        assert "TimestampFormat" in config_dict
        assert config_dict["TimestampFormat"] == timestamp_fmt
    else:
        assert "TimestampFormat" not in config_dict


@given(
    title=valid_titles,
    bucket=bucket_names,
    kms_key=st.one_of(st.none(), kms_keys),
    prefix=st.one_of(st.none(), s3_prefixes)
)
def test_data_output_configuration_with_kms(title, bucket, kms_key, prefix):
    """Test DataOutputConfiguration with optional KMS key."""
    s3_config = le.S3OutputConfiguration(Bucket=bucket)
    if prefix is not None:
        s3_config.Prefix = prefix
    
    output_config = le.DataOutputConfiguration(
        title=title,
        S3OutputConfiguration=s3_config
    )
    
    if kms_key is not None:
        output_config.KmsKeyId = kms_key
    
    config_dict = output_config.to_dict()
    
    # S3OutputConfiguration is required
    assert "S3OutputConfiguration" in config_dict
    assert "Bucket" in config_dict["S3OutputConfiguration"]
    
    # KmsKeyId is optional
    if kms_key is not None:
        assert "KmsKeyId" in config_dict
        assert config_dict["KmsKeyId"] == kms_key
    else:
        assert "KmsKeyId" not in config_dict


@given(title=valid_titles)
def test_inference_scheduler_missing_required_properties_raises(title):
    """Test that InferenceScheduler raises when required properties are missing."""
    # Create scheduler without required properties
    scheduler = le.InferenceScheduler(title)
    
    # Should raise when trying to validate
    with pytest.raises(ValueError, match="required in type"):
        scheduler.to_dict()


@given(
    title1=valid_titles,
    title2=valid_titles,
    bucket=bucket_names,
    prefix=s3_prefixes,
)
def test_equality_and_hash_consistency(title1, title2, bucket, prefix):
    """Test that equal objects have equal hashes."""
    # Create two identical configurations
    config1 = le.S3InputConfiguration(
        title=title1,
        Bucket=bucket,
        Prefix=prefix
    )
    
    config2 = le.S3InputConfiguration(
        title=title1,  # Same title as config1
        Bucket=bucket,
        Prefix=prefix
    )
    
    # Same data, same title = equal
    if title1 == title2:
        assert config1 == config2
        assert hash(config1) == hash(config2)
    
    # Create with different title
    config3 = le.S3InputConfiguration(
        title=title2,
        Bucket=bucket,
        Prefix=prefix
    )
    
    # Different titles = not equal
    if title1 != title2:
        assert config1 != config3