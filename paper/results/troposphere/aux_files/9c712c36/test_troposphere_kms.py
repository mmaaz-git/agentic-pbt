"""Property-based tests for troposphere.kms module"""

import sys
import os

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import troposphere.kms as kms
from troposphere.validators.kms import (
    key_usage_type,
    validate_pending_window_in_days,
    policytypes,
    validate_tags_or_list
)
from troposphere.validators import boolean, integer_range
from troposphere import Tags, AWSHelperFn, Ref


# Test key_usage_type validator
@given(st.text())
def test_key_usage_type_invalid_strings(value):
    """The key_usage_type validator should only accept ENCRYPT_DECRYPT or SIGN_VERIFY"""
    if value not in ["ENCRYPT_DECRYPT", "SIGN_VERIFY"]:
        with pytest.raises(ValueError, match='KeyUsage must be one of'):
            key_usage_type(value)
    else:
        # Should not raise for valid values
        assert key_usage_type(value) == value


@given(st.sampled_from(["ENCRYPT_DECRYPT", "SIGN_VERIFY"]))
def test_key_usage_type_valid(value):
    """Valid key usage types should be returned unchanged"""
    assert key_usage_type(value) == value


# Test validate_pending_window_in_days
@given(st.integers())
def test_pending_window_validation(value):
    """PendingWindowInDays must be between 7 and 30 inclusive"""
    if 7 <= value <= 30:
        # Should not raise for valid range
        assert validate_pending_window_in_days(value) == value
    else:
        # Should raise for out of range
        with pytest.raises(ValueError, match="Integer must be between"):
            validate_pending_window_in_days(value)


# Test boolean validator
@given(st.one_of(
    st.booleans(),
    st.integers(),
    st.text(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_validator(value):
    """Boolean validator should only accept specific true/false values"""
    true_values = [True, 1, "1", "true", "True"]
    false_values = [False, 0, "0", "false", "False"]
    
    if value in true_values:
        assert boolean(value) is True
    elif value in false_values:
        assert boolean(value) is False
    else:
        with pytest.raises(ValueError):
            boolean(value)


# Test integer_range function
@given(
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers()
)
def test_integer_range_validator(min_val, max_val, test_val):
    """integer_range should create a validator that checks bounds"""
    assume(min_val <= max_val)  # Ensure valid range
    assume(abs(min_val) < 1e10)  # Keep numbers reasonable
    assume(abs(max_val) < 1e10)
    
    validator = integer_range(min_val, max_val)
    
    if min_val <= test_val <= max_val:
        # Should not raise for valid range
        assert validator(test_val) == test_val
    else:
        # Should raise for out of range
        with pytest.raises(ValueError, match="Integer must be between"):
            validator(test_val)


# Test that integer_range accepts float bounds but validates integers
@given(
    st.floats(min_value=-1000, max_value=1000, allow_nan=False),
    st.floats(min_value=-1000, max_value=1000, allow_nan=False)
)
def test_integer_range_with_float_bounds(min_val, max_val):
    """integer_range should accept float bounds"""
    assume(min_val <= max_val)
    
    validator = integer_range(min_val, max_val)
    
    # Test with an integer in range
    test_val = int((min_val + max_val) / 2)
    if min_val <= test_val <= max_val:
        assert validator(test_val) == test_val


# Test KMS Key object validation
@given(st.text())
def test_kms_key_title_validation(title):
    """KMS Key titles must be alphanumeric only"""
    # The title validator checks for alphanumeric characters only
    is_valid = title and all(c.isalnum() for c in title)
    
    if is_valid:
        # Should create successfully with valid title
        key = kms.Key(title)
        assert key.title == title
    else:
        # Should raise for invalid title
        with pytest.raises(ValueError, match='Name .* not alphanumeric'):
            kms.Key(title)


# Test Alias title validation
@given(st.text())
def test_kms_alias_title_validation(title):
    """KMS Alias titles must be alphanumeric only"""
    is_valid = title and all(c.isalnum() for c in title)
    
    if is_valid:
        # Note: Alias requires AliasName and TargetKeyId
        alias = kms.Alias(title, AliasName="alias/test", TargetKeyId="key-123")
        assert alias.title == title
    else:
        with pytest.raises(ValueError, match='Name .* not alphanumeric'):
            kms.Alias(title, AliasName="alias/test", TargetKeyId="key-123")


# Test required properties validation for Alias
@given(
    st.text().filter(lambda x: x and all(c.isalnum() for c in x)),  # Valid title
    st.booleans(),  # Whether to include AliasName
    st.booleans()   # Whether to include TargetKeyId
)
def test_alias_required_properties(title, include_alias_name, include_target_key):
    """Alias requires both AliasName and TargetKeyId properties"""
    kwargs = {}
    if include_alias_name:
        kwargs['AliasName'] = 'alias/test'
    if include_target_key:
        kwargs['TargetKeyId'] = 'key-123'
    
    if include_alias_name and include_target_key:
        # Should work with both required properties
        alias = kms.Alias(title, **kwargs)
        alias.to_dict()  # This triggers validation
    else:
        # Should fail validation when missing required properties
        alias = kms.Alias(title, **kwargs)
        with pytest.raises(ValueError, match="Resource .* required"):
            alias.to_dict()


# Test ReplicaKey required properties
@given(
    st.text().filter(lambda x: x and all(c.isalnum() for c in x)),  # Valid title
    st.booleans(),  # Whether to include KeyPolicy
    st.booleans()   # Whether to include PrimaryKeyArn
)
def test_replica_key_required_properties(title, include_policy, include_arn):
    """ReplicaKey requires both KeyPolicy and PrimaryKeyArn"""
    kwargs = {}
    if include_policy:
        kwargs['KeyPolicy'] = {'Version': '2012-10-17'}
    if include_arn:
        kwargs['PrimaryKeyArn'] = 'arn:aws:kms:us-east-1:123456789012:key/12345678'
    
    if include_policy and include_arn:
        # Should work with both required properties
        replica = kms.ReplicaKey(title, **kwargs)
        replica.to_dict()
    else:
        # Should fail validation when missing required properties
        replica = kms.ReplicaKey(title, **kwargs)
        with pytest.raises(ValueError, match="Resource .* required"):
            replica.to_dict()


# Test PendingWindowInDays property on Key
@given(
    st.text().filter(lambda x: x and all(c.isalnum() for c in x)),
    st.integers()
)
def test_key_pending_window_property(title, days):
    """Key's PendingWindowInDays should validate using validate_pending_window_in_days"""
    key = kms.Key(title)
    
    if 7 <= days <= 30:
        # Should accept valid range
        key.PendingWindowInDays = days
        assert key.PendingWindowInDays == days
    else:
        # Should raise for invalid range
        with pytest.raises(ValueError, match="Integer must be between"):
            key.PendingWindowInDays = days


# Test KeyUsage property on Key
@given(
    st.text().filter(lambda x: x and all(c.isalnum() for c in x)),
    st.text()
)
def test_key_usage_property(title, usage):
    """Key's KeyUsage should validate using key_usage_type"""
    key = kms.Key(title)
    
    if usage in ["ENCRYPT_DECRYPT", "SIGN_VERIFY"]:
        key.KeyUsage = usage
        assert key.KeyUsage == usage
    else:
        with pytest.raises(ValueError, match="KeyUsage must be one of"):
            key.KeyUsage = usage


# Test boolean properties on Key
@given(
    st.text().filter(lambda x: x and all(c.isalnum() for c in x)),
    st.one_of(
        st.booleans(),
        st.integers(),
        st.text(),
        st.floats(),
        st.none()
    )
)
def test_key_boolean_properties(title, value):
    """Key's boolean properties should validate using boolean validator"""
    key = kms.Key(title)
    
    true_values = [True, 1, "1", "true", "True"]
    false_values = [False, 0, "0", "false", "False"]
    
    boolean_props = ['EnableKeyRotation', 'Enabled', 'MultiRegion', 'BypassPolicyLockoutSafetyCheck']
    
    for prop in boolean_props:
        if value in true_values:
            setattr(key, prop, value)
            assert getattr(key, prop) is True
        elif value in false_values:
            setattr(key, prop, value)
            assert getattr(key, prop) is False
        else:
            with pytest.raises((ValueError, TypeError)):
                setattr(key, prop, value)


if __name__ == "__main__":
    # Run with increased examples for more thorough testing
    pytest.main([__file__, "-v", "--tb=short"])