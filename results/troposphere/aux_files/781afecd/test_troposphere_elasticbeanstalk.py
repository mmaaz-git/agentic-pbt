#!/usr/bin/env python3
"""Property-based tests for troposphere.elasticbeanstalk module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.elasticbeanstalk as eb
from troposphere.validators.elasticbeanstalk import (
    validate_tier_name, 
    validate_tier_type,
    WebServer,
    Worker,
    WebServerType,
    WorkerType
)


# Test 1: Validator functions should only accept valid values and return them unchanged
@given(st.text())
def test_validate_tier_name_invalid(name):
    """validate_tier_name should only accept 'WebServer' or 'Worker'."""
    assume(name not in [WebServer, Worker])
    try:
        result = validate_tier_name(name)
        # If we get here, the validator accepted an invalid name
        assert False, f"validate_tier_name incorrectly accepted '{name}'"
    except ValueError as e:
        # This is expected for invalid names
        assert "Tier name needs to be one of" in str(e)


@given(st.sampled_from([WebServer, Worker]))
def test_validate_tier_name_valid(name):
    """validate_tier_name should accept and return valid tier names unchanged."""
    result = validate_tier_name(name)
    assert result == name


@given(st.text())
def test_validate_tier_type_invalid(tier_type):
    """validate_tier_type should only accept 'Standard' or 'SQS/HTTP'."""
    assume(tier_type not in [WebServerType, WorkerType])
    try:
        result = validate_tier_type(tier_type)
        assert False, f"validate_tier_type incorrectly accepted '{tier_type}'"
    except ValueError as e:
        assert "Tier type needs to be one of" in str(e)


@given(st.sampled_from([WebServerType, WorkerType]))
def test_validate_tier_type_valid(tier_type):
    """validate_tier_type should accept and return valid tier types unchanged."""
    result = validate_tier_type(tier_type)
    assert result == tier_type


# Test 2: Title validation - must be alphanumeric only
@given(st.text(min_size=1))
def test_title_validation(title):
    """AWSObject titles must be alphanumeric only."""
    is_alphanumeric = title.isalnum()
    
    try:
        app = eb.Application(title)
        # If we get here, the title was accepted
        assert is_alphanumeric, f"Non-alphanumeric title '{title}' was incorrectly accepted"
    except ValueError as e:
        # Title was rejected
        assert not is_alphanumeric, f"Alphanumeric title '{title}' was incorrectly rejected"
        assert 'not alphanumeric' in str(e)


# Test 3: Required properties validation
@given(
    st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122), min_size=1).filter(str.isalnum),
    st.text(min_size=1),
    st.text(min_size=1),
    st.text(min_size=1)
)
def test_required_properties_application_version(title, app_name, s3_bucket, s3_key):
    """ApplicationVersion requires ApplicationName and SourceBundle."""
    # Create a valid ApplicationVersion
    av = eb.ApplicationVersion(
        title,
        ApplicationName=app_name,
        SourceBundle=eb.SourceBundle(
            S3Bucket=s3_bucket,
            S3Key=s3_key
        )
    )
    
    # Should not raise when all required props are present
    av.to_dict()
    
    # Test missing ApplicationName
    av2 = eb.ApplicationVersion(title)
    av2.SourceBundle = eb.SourceBundle(S3Bucket=s3_bucket, S3Key=s3_key)
    try:
        av2.to_dict()
        assert False, "Missing ApplicationName should raise ValueError"
    except ValueError as e:
        assert "ApplicationName" in str(e)
    
    # Test missing SourceBundle
    av3 = eb.ApplicationVersion(title)
    av3.ApplicationName = app_name
    try:
        av3.to_dict()
        assert False, "Missing SourceBundle should raise ValueError"  
    except ValueError as e:
        assert "SourceBundle" in str(e)


# Test 4: SourceBundle requires both S3Bucket and S3Key
@given(st.text(min_size=1), st.text(min_size=1))
def test_source_bundle_required_properties(s3_bucket, s3_key):
    """SourceBundle requires both S3Bucket and S3Key."""
    # Valid SourceBundle
    sb = eb.SourceBundle(S3Bucket=s3_bucket, S3Key=s3_key)
    sb.to_dict()  # Should not raise
    
    # Missing S3Bucket
    sb2 = eb.SourceBundle()
    sb2.S3Key = s3_key
    try:
        sb2.to_dict()
        assert False, "Missing S3Bucket should raise ValueError"
    except ValueError as e:
        assert "S3Bucket" in str(e)
    
    # Missing S3Key
    sb3 = eb.SourceBundle()
    sb3.S3Bucket = s3_bucket
    try:
        sb3.to_dict()
        assert False, "Missing S3Key should raise ValueError"
    except ValueError as e:
        assert "S3Key" in str(e)


# Test 5: Round-trip property for Application
@given(
    st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122), min_size=1, max_size=50).filter(str.isalnum),
    st.text(max_size=200),
    st.text(max_size=100).map(lambda x: x if x else None)
)
def test_application_round_trip(title, app_name, description):
    """Application.from_dict(app.to_dict()) should reconstruct the object."""
    app = eb.Application(title)
    
    # Set optional properties
    if app_name:
        app.ApplicationName = app_name
    if description:
        app.Description = description
    
    # Convert to dict and back
    app_dict = app.to_dict()
    
    # from_dict expects the Properties dict, not the full resource dict
    if "Properties" in app_dict:
        props = app_dict["Properties"]
        app2 = eb.Application.from_dict(title, props)
        
        # Compare the dictionaries
        app2_dict = app2.to_dict()
        assert app_dict == app2_dict


# Test 6: Round-trip for Environment with various properties
@given(
    st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122), min_size=1, max_size=50).filter(str.isalnum),
    st.text(min_size=1, max_size=100),
    st.text(max_size=63).filter(lambda x: x.isalnum() if x else True).map(lambda x: x if x else None),
    st.text(max_size=200).map(lambda x: x if x else None)
)
def test_environment_round_trip(title, app_name, cname_prefix, description):
    """Environment.from_dict(env.to_dict()) should reconstruct the object."""
    env = eb.Environment(title, ApplicationName=app_name)
    
    if cname_prefix:
        env.CNAMEPrefix = cname_prefix
    if description:
        env.Description = description
    
    env_dict = env.to_dict()
    
    if "Properties" in env_dict:
        props = env_dict["Properties"]
        env2 = eb.Environment.from_dict(title, props)
        
        env2_dict = env2.to_dict()
        assert env_dict == env2_dict


# Test 7: Tier property validation
@given(
    st.sampled_from([WebServer, Worker]),
    st.sampled_from([WebServerType, WorkerType]),
    st.text(max_size=20).map(lambda x: x if x else None)
)
def test_tier_property(name, tier_type, version):
    """Tier should validate Name and Type correctly."""
    tier = eb.Tier()
    
    # These should work with valid values
    tier.Name = name
    tier.Type = tier_type
    if version:
        tier.Version = version
    
    tier_dict = tier.to_dict()
    assert tier_dict.get("Name") == name
    assert tier_dict.get("Type") == tier_type
    if version:
        assert tier_dict.get("Version") == version


# Test 8: OptionSetting required properties
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100),
    st.text(max_size=100).map(lambda x: x if x else None),
    st.text(max_size=200).map(lambda x: x if x else None)
)
def test_option_setting_properties(namespace, option_name, resource_name, value):
    """OptionSetting requires Namespace and OptionName."""
    # Valid OptionSetting
    os = eb.OptionSetting(
        Namespace=namespace,
        OptionName=option_name
    )
    
    if resource_name:
        os.ResourceName = resource_name
    if value:
        os.Value = value
    
    os_dict = os.to_dict()
    assert os_dict["Namespace"] == namespace
    assert os_dict["OptionName"] == option_name
    
    # Test missing required properties
    os2 = eb.OptionSetting()
    os2.OptionName = option_name
    try:
        os2.to_dict()
        assert False, "Missing Namespace should raise ValueError"
    except ValueError as e:
        assert "Namespace" in str(e)


# Test 9: List properties should only accept lists
@given(
    st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122), min_size=1).filter(str.isalnum),
    st.text(min_size=1),
    st.one_of(
        st.text(),
        st.integers(),
        st.dictionaries(st.text(), st.text()),
        st.booleans()
    )
)
def test_list_property_type_validation(title, app_name, invalid_value):
    """List properties should reject non-list values."""
    env = eb.Environment(title, ApplicationName=app_name)
    
    # OptionSettings expects a list
    try:
        env.OptionSettings = invalid_value
        # If it's not a list, this should have raised
        if not isinstance(invalid_value, list):
            assert False, f"OptionSettings accepted non-list value: {type(invalid_value)}"
    except (TypeError, AttributeError) as e:
        # Expected for non-list values
        if isinstance(invalid_value, list):
            assert False, f"OptionSettings rejected list value"


# Test 10: MaxAgeRule and MaxCountRule integer validation
@given(
    st.booleans(),
    st.booleans(),
    st.one_of(st.integers(min_value=1, max_value=365), st.none())
)
def test_max_age_rule_properties(delete_source, enabled, max_age):
    """MaxAgeRule properties should accept valid types."""
    rule = eb.MaxAgeRule()
    
    rule.DeleteSourceFromS3 = delete_source
    rule.Enabled = enabled
    if max_age is not None:
        rule.MaxAgeInDays = max_age
    
    rule_dict = rule.to_dict()
    assert rule_dict["DeleteSourceFromS3"] == delete_source
    assert rule_dict["Enabled"] == enabled
    if max_age is not None:
        assert rule_dict["MaxAgeInDays"] == max_age


@given(
    st.booleans(),
    st.booleans(),
    st.one_of(st.integers(min_value=1, max_value=1000), st.none())
)
def test_max_count_rule_properties(delete_source, enabled, max_count):
    """MaxCountRule properties should accept valid types."""
    rule = eb.MaxCountRule()
    
    rule.DeleteSourceFromS3 = delete_source
    rule.Enabled = enabled
    if max_count is not None:
        rule.MaxCount = max_count
    
    rule_dict = rule.to_dict()
    assert rule_dict["DeleteSourceFromS3"] == delete_source
    assert rule_dict["Enabled"] == enabled
    if max_count is not None:
        assert rule_dict["MaxCount"] == max_count


if __name__ == "__main__":
    print("Running property-based tests for troposphere.elasticbeanstalk...")
    
    # Run with increased examples for better coverage
    settings.register_profile("thorough", max_examples=200)
    settings.load_profile("thorough")