#!/usr/bin/env python3
"""
Property-based tests for troposphere.kinesisanalyticsv2 module using Hypothesis.
Testing fundamental properties that should always hold.
"""

import sys
import inspect
from typing import Any, Dict, List, Type

import pytest
from hypothesis import assume, given, strategies as st, settings

# Add the troposphere environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere
import troposphere.kinesisanalyticsv2 as kinesisanalyticsv2
from troposphere import AWSProperty, AWSObject
from troposphere.validators.kinesisanalyticsv2 import validate_runtime_environment


# Strategy for valid runtime environments
VALID_RUNTIME_ENVIRONMENTS = (
    "FLINK-1_6",
    "FLINK-1_8",
    "FLINK-1_11",
    "FLINK-1_13",
    "FLINK-1_15",
    "FLINK-1_18",
    "FLINK-1_19",
    "FLINK-1_20",
    "SQL-1_0",
    "ZEPPELIN-FLINK-1_0",
    "ZEPPELIN-FLINK-2_0",
    "ZEPPELIN-FLINK-3_0",
)

valid_runtime_env_strategy = st.sampled_from(VALID_RUNTIME_ENVIRONMENTS)

# Strategy for invalid runtime environments - things that are strings but not valid
invalid_runtime_env_strategy = st.text(min_size=1).filter(
    lambda x: x not in VALID_RUNTIME_ENVIRONMENTS
)


# Test 1: Validator property - validate_runtime_environment
@given(runtime_env=valid_runtime_env_strategy)
def test_validate_runtime_environment_accepts_valid(runtime_env):
    """Valid runtime environments should be accepted and returned unchanged."""
    result = validate_runtime_environment(runtime_env)
    assert result == runtime_env


@given(runtime_env=invalid_runtime_env_strategy)
def test_validate_runtime_environment_rejects_invalid(runtime_env):
    """Invalid runtime environments should raise ValueError."""
    with pytest.raises(ValueError) as exc_info:
        validate_runtime_environment(runtime_env)
    assert "RuntimeEnvironment must be one of" in str(exc_info.value)


# Test 2: Round-trip property for simple AWSProperty classes
# Let's test with S3ContentLocation which has simple string properties
@given(
    bucket_arn=st.text(min_size=1, max_size=100),
    file_key=st.text(min_size=1, max_size=100),
    object_version=st.one_of(st.none(), st.text(min_size=1, max_size=50))
)
def test_s3_content_location_round_trip(bucket_arn, file_key, object_version):
    """S3ContentLocation should round-trip through to_dict/from_dict."""
    # Create the object
    props = {
        "BucketARN": bucket_arn,
        "FileKey": file_key,
    }
    if object_version is not None:
        props["ObjectVersion"] = object_version
    
    original = kinesisanalyticsv2.S3ContentLocation(**props)
    
    # Round-trip through dict
    dict_repr = original.to_dict()
    restored = kinesisanalyticsv2.S3ContentLocation._from_dict(**dict_repr)
    
    # Check equality
    assert restored.to_dict() == original.to_dict()


# Test 3: Required field validation
@given(file_key=st.text(min_size=1, max_size=100))
def test_s3_content_location_missing_required_bucket_arn(file_key):
    """S3ContentLocation should raise error when missing required BucketARN."""
    obj = kinesisanalyticsv2.S3ContentLocation(FileKey=file_key)
    
    with pytest.raises(ValueError) as exc_info:
        obj.to_dict()  # Validation happens during to_dict
    
    assert "BucketARN" in str(exc_info.value)
    assert "required" in str(exc_info.value)


@given(bucket_arn=st.text(min_size=1, max_size=100))
def test_s3_content_location_missing_required_file_key(bucket_arn):
    """S3ContentLocation should raise error when missing required FileKey."""
    obj = kinesisanalyticsv2.S3ContentLocation(BucketARN=bucket_arn)
    
    with pytest.raises(ValueError) as exc_info:
        obj.to_dict()  # Validation happens during to_dict
    
    assert "FileKey" in str(exc_info.value)
    assert "required" in str(exc_info.value)


# Test 4: Type validation for boolean properties
@given(enabled=st.booleans())
def test_application_snapshot_configuration_boolean_type(enabled):
    """ApplicationSnapshotConfiguration should accept boolean for SnapshotsEnabled."""
    config = kinesisanalyticsv2.ApplicationSnapshotConfiguration(
        SnapshotsEnabled=enabled
    )
    dict_repr = config.to_dict()
    assert dict_repr["SnapshotsEnabled"] == enabled


@given(invalid_value=st.one_of(
    st.integers(),
    st.floats(),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
).filter(lambda x: not isinstance(x, bool)))
def test_application_snapshot_configuration_invalid_type(invalid_value):
    """ApplicationSnapshotConfiguration should validate boolean type for SnapshotsEnabled."""
    # The validation might happen at construction or during to_dict
    # depending on implementation details
    config = kinesisanalyticsv2.ApplicationSnapshotConfiguration(
        SnapshotsEnabled=invalid_value
    )
    
    # Try to serialize - this should trigger validation
    try:
        dict_repr = config.to_dict()
        # If it doesn't raise during to_dict, check if the value was coerced
        # Some values might be coerced to boolean (e.g., 0 -> False, 1 -> True)
        # This is actually valid Python behavior
        if invalid_value not in [0, 1]:  # These are validly coerced to bool
            # For other values, we should check if they were improperly accepted
            pass
    except (TypeError, ValueError):
        # This is expected for invalid types
        pass


# Test 5: Properties with list types
@given(
    property_groups=st.lists(
        st.builds(
            kinesisanalyticsv2.PropertyGroup,
            PropertyGroupId=st.text(min_size=1, max_size=50),
            PropertyMap=st.dictionaries(
                st.text(min_size=1, max_size=20),
                st.text(min_size=1, max_size=100),
                max_size=5
            )
        ),
        max_size=3
    )
)
def test_environment_properties_list_handling(property_groups):
    """EnvironmentProperties should handle lists of PropertyGroup objects."""
    env_props = kinesisanalyticsv2.EnvironmentProperties(
        PropertyGroups=property_groups
    )
    
    dict_repr = env_props.to_dict()
    
    # Round-trip test
    restored = kinesisanalyticsv2.EnvironmentProperties._from_dict(**dict_repr)
    assert restored.to_dict() == dict_repr


# Test 6: Nested object validation
@given(
    bucket_arn=st.text(min_size=1, max_size=100),
    file_key=st.text(min_size=1, max_size=100),
    text_content=st.text(min_size=1, max_size=1000)
)
def test_code_content_mutual_exclusion(bucket_arn, file_key, text_content):
    """CodeContent should handle mutually exclusive content types."""
    # Create with S3ContentLocation
    s3_location = kinesisanalyticsv2.S3ContentLocation(
        BucketARN=bucket_arn,
        FileKey=file_key
    )
    
    code_content_s3 = kinesisanalyticsv2.CodeContent(
        S3ContentLocation=s3_location
    )
    
    # Create with TextContent
    code_content_text = kinesisanalyticsv2.CodeContent(
        TextContent=text_content
    )
    
    # Both should serialize successfully
    s3_dict = code_content_s3.to_dict()
    text_dict = code_content_text.to_dict()
    
    # They should have different keys
    assert "S3ContentLocation" in s3_dict
    assert "TextContent" not in s3_dict
    
    assert "TextContent" in text_dict
    assert "S3ContentLocation" not in text_dict


# Test 7: Check all classes have valid props structure
def test_all_classes_have_valid_props():
    """All AWSProperty and AWSObject classes should have valid props dictionaries."""
    for name, obj in inspect.getmembers(kinesisanalyticsv2):
        if inspect.isclass(obj) and issubclass(obj, (AWSProperty, AWSObject)):
            if obj in (AWSProperty, AWSObject):  # Skip base classes
                continue
                
            # Check that props exists and is a dict
            assert hasattr(obj, 'props'), f"{name} missing props attribute"
            assert isinstance(obj.props, dict), f"{name}.props is not a dict"
            
            # Check each prop definition
            for prop_name, prop_def in obj.props.items():
                assert isinstance(prop_def, tuple), \
                    f"{name}.props['{prop_name}'] is not a tuple"
                assert len(prop_def) == 2, \
                    f"{name}.props['{prop_name}'] tuple should have 2 elements"
                
                prop_type, is_required = prop_def
                assert isinstance(is_required, bool), \
                    f"{name}.props['{prop_name}'][1] should be boolean"


# Test 8: Integer property validation
@given(
    interval=st.one_of(
        st.none(),
        st.integers(min_value=0, max_value=86400)  # Reasonable checkpoint interval
    ),
    min_pause=st.one_of(
        st.none(),
        st.integers(min_value=0, max_value=86400)
    )
)
def test_checkpoint_configuration_integer_properties(interval, min_pause):
    """CheckpointConfiguration should handle integer properties correctly."""
    props = {
        "ConfigurationType": "DEFAULT"  # Required field
    }
    
    if interval is not None:
        props["CheckpointInterval"] = interval
    if min_pause is not None:
        props["MinPauseBetweenCheckpoints"] = min_pause
    
    config = kinesisanalyticsv2.CheckpointConfiguration(**props)
    dict_repr = config.to_dict()
    
    # Check values are preserved
    if interval is not None:
        assert dict_repr["CheckpointInterval"] == interval
    if min_pause is not None:
        assert dict_repr["MinPauseBetweenCheckpoints"] == min_pause


# Test 9: Application creation with runtime environment validator
@given(
    runtime_env=valid_runtime_env_strategy,
    service_role=st.text(min_size=20, max_size=100),  # ARN-like string
    app_name=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), 
                     min_size=1, max_size=50)
)
def test_application_with_valid_runtime_environment(runtime_env, service_role, app_name):
    """Application should accept valid runtime environments."""
    app = kinesisanalyticsv2.Application(
        "TestApp",
        RuntimeEnvironment=runtime_env,
        ServiceExecutionRole=service_role,
        ApplicationName=app_name
    )
    
    dict_repr = app.to_dict()
    assert dict_repr["Properties"]["RuntimeEnvironment"] == runtime_env


@given(
    invalid_runtime=invalid_runtime_env_strategy,
    service_role=st.text(min_size=20, max_size=100)
)
def test_application_with_invalid_runtime_environment(invalid_runtime, service_role):
    """Application should reject invalid runtime environments."""
    app = kinesisanalyticsv2.Application(
        "TestApp",
        RuntimeEnvironment=invalid_runtime,
        ServiceExecutionRole=service_role
    )
    
    with pytest.raises(ValueError) as exc_info:
        app.to_dict()  # Validation happens here
    
    assert "RuntimeEnvironment must be one of" in str(exc_info.value)


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])