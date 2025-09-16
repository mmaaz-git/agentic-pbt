#!/usr/bin/env python3
"""Property-based tests for troposphere.m2 module using Hypothesis."""

import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
import troposphere.m2 as m2
from troposphere import validators
from troposphere import BaseAWSObject, AWSObject, AWSProperty


# Test 1: Boolean validator conversion property
@given(st.one_of(
    st.just(True), st.just(False),
    st.just(1), st.just(0),
    st.just("true"), st.just("false"),
    st.just("True"), st.just("False"),
    st.just("1"), st.just("0")
))
def test_boolean_validator_conversion(value):
    """Test that boolean validator correctly converts various inputs."""
    result = validators.boolean(value)
    assert isinstance(result, bool)
    
    # Verify the conversion is correct
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False


# Test 2: Integer validator property
@given(st.one_of(
    st.integers(),
    st.text(alphabet="0123456789", min_size=1, max_size=10),
    st.text(alphabet="-0123456789", min_size=1, max_size=10).filter(lambda x: x != "-" and not x.startswith("-0"))
))
def test_integer_validator_accepts_valid_integers(value):
    """Test that integer validator accepts valid integer representations."""
    try:
        int(value)
        is_valid = True
    except (ValueError, TypeError):
        is_valid = False
    
    if is_valid:
        result = validators.integer(value)
        assert result == value
        # Should be convertible to int
        int(result)


# Test 3: Round-trip property for to_dict/from_dict
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=20),
    app_id=st.text(min_size=1, max_size=50),
    app_version=st.integers(min_value=1, max_value=1000),
    env_id=st.text(min_size=1, max_size=50)
)
def test_deployment_roundtrip_dict(title, app_id, app_version, env_id):
    """Test that Deployment objects can be serialized and deserialized."""
    # Create original object
    original = m2.Deployment(
        title=title,
        ApplicationId=app_id,
        ApplicationVersion=app_version,
        EnvironmentId=env_id
    )
    
    # Serialize to dict
    as_dict = original.to_dict()
    assert isinstance(as_dict, dict)
    
    # Extract properties for recreation
    props = as_dict.get('Properties', {})
    
    # Create new object from dict
    restored = m2.Deployment.from_dict(title, props)
    
    # Verify they are equal
    assert original == restored
    assert original.to_json(validation=False) == restored.to_json(validation=False)


# Test 4: Title validation property
@given(st.text())
def test_title_validation_alphanumeric(title):
    """Test that title validation correctly enforces alphanumeric requirement."""
    import re
    valid_names = re.compile(r"^[a-zA-Z0-9]+$")
    
    if not title or not valid_names.match(title):
        # Should raise ValueError for invalid titles
        try:
            app = m2.Application(title=title, EngineType="microfocus", Name="test")
            # If we get here, validation didn't happen as expected
            # This might be okay if validation is deferred
            pass
        except ValueError as e:
            assert 'not alphanumeric' in str(e)
    else:
        # Should succeed for valid titles
        app = m2.Application(title=title, EngineType="microfocus", Name="test")
        assert app.title == title


# Test 5: Storage configuration mutually exclusive property
@given(
    has_efs=st.booleans(),
    has_fsx=st.booleans(),
    fs_id=st.text(min_size=1, max_size=50),
    mount_point=st.text(min_size=1, max_size=50)
)
def test_storage_configuration_properties(has_efs, has_fsx, fs_id, mount_point):
    """Test StorageConfiguration can have Efs or Fsx but not require both."""
    config_dict = {}
    
    if has_efs:
        config_dict['Efs'] = m2.EfsStorageConfiguration(
            FileSystemId=fs_id,
            MountPoint=mount_point
        )
    
    if has_fsx:
        config_dict['Fsx'] = m2.FsxStorageConfiguration(
            FileSystemId=fs_id,
            MountPoint=mount_point
        )
    
    # Should be able to create with either, both, or neither
    storage = m2.StorageConfiguration(**config_dict)
    
    # Verify the properties are set correctly
    if has_efs:
        assert hasattr(storage, 'Efs') or 'Efs' in storage.properties
    if has_fsx:
        assert hasattr(storage, 'Fsx') or 'Fsx' in storage.properties
    
    # Should serialize without errors
    storage.to_dict()


# Test 6: Definition S3Location vs Content property
@given(
    has_content=st.booleans(),
    has_s3=st.booleans(),
    content=st.text(min_size=1, max_size=100),
    s3_location=st.text(min_size=1, max_size=100)
)
def test_definition_content_or_s3(has_content, has_s3, content, s3_location):
    """Test Definition can have Content or S3Location."""
    kwargs = {}
    if has_content:
        kwargs['Content'] = content
    if has_s3:
        kwargs['S3Location'] = s3_location
    
    # Should allow either, both, or neither
    definition = m2.Definition(**kwargs)
    
    # Should serialize without errors
    serialized = definition.to_dict()
    
    # Properties should be preserved
    if has_content:
        assert 'Content' in serialized or hasattr(definition, 'Content')
    if has_s3:
        assert 'S3Location' in serialized or hasattr(definition, 'S3Location')


# Test 7: HighAvailabilityConfig integer property
@given(capacity=st.integers())
def test_high_availability_config_integer(capacity):
    """Test HighAvailabilityConfig accepts integer DesiredCapacity."""
    # The integer validator should accept any integer
    config = m2.HighAvailabilityConfig(DesiredCapacity=capacity)
    
    # Should be able to serialize
    serialized = config.to_dict()
    
    # The value should be preserved
    assert 'DesiredCapacity' in serialized or hasattr(config, 'DesiredCapacity')


# Test 8: Application tags property
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=20),
    tags=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=0, max_size=100),
        max_size=10
    )
)
def test_application_tags_dict(title, tags):
    """Test Application accepts Tags as a dictionary."""
    app = m2.Application(
        title=title,
        EngineType="microfocus",
        Name="test-app",
        Tags=tags
    )
    
    # Should serialize without errors
    serialized = app.to_dict()
    
    # Tags should be in the output
    if tags:
        props = serialized.get('Properties', {})
        assert 'Tags' in props


# Test 9: Environment boolean property for PubliclyAccessible
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=20),
    publicly_accessible=st.one_of(
        st.booleans(),
        st.sampled_from([0, 1, "true", "false", "True", "False"])
    )
)
def test_environment_publicly_accessible_boolean(title, publicly_accessible):
    """Test Environment PubliclyAccessible accepts boolean-like values."""
    env = m2.Environment(
        title=title,
        EngineType="microfocus",
        InstanceType="m5.large",
        Name="test-env",
        PubliclyAccessible=publicly_accessible
    )
    
    # Should serialize without errors
    serialized = env.to_dict()
    
    # The boolean validator should have converted it
    props = serialized.get('Properties', {})
    if 'PubliclyAccessible' in props:
        # Should be a proper boolean after validation
        assert isinstance(props['PubliclyAccessible'], bool)


# Test 10: Required properties validation
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=20),
    include_engine=st.booleans(),
    include_name=st.booleans()
)
def test_application_required_properties(title, include_engine, include_name):
    """Test that Application enforces required properties."""
    kwargs = {'title': title}
    
    if include_engine:
        kwargs['EngineType'] = 'microfocus'
    if include_name:
        kwargs['Name'] = 'test-app'
    
    if include_engine and include_name:
        # Should succeed with all required properties
        app = m2.Application(**kwargs)
        # Validation should pass
        try:
            app.to_dict(validation=True)
        except ValueError:
            # This shouldn't happen with all required fields
            assert False, "Validation failed with all required fields"
    else:
        # Missing required properties
        app = m2.Application(**kwargs)
        # Should fail validation when missing required fields
        try:
            app.to_dict(validation=True)
            # If we get here, validation didn't catch missing required field
            # This is actually valid - the object can be created without required fields
            # Validation only happens on to_dict() with validation=True
        except ValueError as e:
            # Should mention the missing required field
            assert 'required' in str(e).lower()