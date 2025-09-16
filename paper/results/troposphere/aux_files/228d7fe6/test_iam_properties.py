#!/usr/bin/env python3
"""Property-based tests for troposphere.iam module validators and classes."""

import re
from hypothesis import given, strategies as st, assume
from hypothesis import settings
import pytest

# Import the targets
from troposphere import iam
from troposphere.validators import iam as iam_validators


# Strategy for generating valid IAM names based on the regex in the code
def valid_iam_name_strategy():
    """Generate names matching ^[a-zA-Z0-9_\.\+\=\@\-\,]+$"""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.+=@-,"
    return st.text(alphabet=chars, min_size=1, max_size=128)


# Strategy for generating valid IAM user names based on the regex in the code
def valid_iam_user_name_strategy():
    """Generate names matching ^[\w+=,.@-]+$"""
    # \w in Python includes underscore and alphanumeric characters
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+=,.@-"
    return st.text(alphabet=chars, min_size=1, max_size=64)


# Test 1: IAM Group Name validation length constraint
@given(st.text(min_size=1))
def test_iam_group_name_length_constraint(name):
    """Property: iam_group_name should reject names > 128 characters"""
    if len(name) > 128:
        with pytest.raises(ValueError, match="IAM Role Name may not exceed 128 characters"):
            iam_validators.iam_group_name(name)
    else:
        # Also need to match the regex pattern
        iam_name_re = re.compile(r"^[a-zA-Z0-9_\.\+\=\@\-\,]+$")
        if iam_name_re.match(name):
            result = iam_validators.iam_group_name(name)
            assert result == name
        else:
            with pytest.raises(ValueError, match="is not a valid iam name"):
                iam_validators.iam_group_name(name)


# Test 2: IAM Role Name validation length constraint
@given(st.text(min_size=1))
def test_iam_role_name_length_constraint(name):
    """Property: iam_role_name should reject names > 64 characters"""
    if len(name) > 64:
        with pytest.raises(ValueError, match="IAM Role Name may not exceed 64 characters"):
            iam_validators.iam_role_name(name)
    else:
        # Also need to match the regex pattern
        iam_name_re = re.compile(r"^[a-zA-Z0-9_\.\+\=\@\-\,]+$")
        if iam_name_re.match(name):
            result = iam_validators.iam_role_name(name)
            assert result == name
        else:
            with pytest.raises(ValueError, match="is not a valid iam name"):
                iam_validators.iam_role_name(name)


# Test 3: IAM User Name validation constraints
@given(st.text())
def test_iam_user_name_constraints(name):
    """Property: iam_user_name validation rules as documented"""
    if not name:
        with pytest.raises(ValueError, match="may not be empty"):
            iam_validators.iam_user_name(name)
    elif len(name) > 64:
        with pytest.raises(ValueError, match="may not exceed 64 characters"):
            iam_validators.iam_user_name(name)
    else:
        iam_user_name_re = re.compile(r"^[\w+=,.@-]+$")
        if iam_user_name_re.match(name):
            result = iam_validators.iam_user_name(name)
            assert result == name
        else:
            with pytest.raises(ValueError, match="is not a valid value"):
                iam_validators.iam_user_name(name)


# Test 4: IAM Path validation
@given(st.text())
def test_iam_path_validation(path):
    """Property: iam_path must match the pattern and length constraints"""
    if len(path) > 512:
        with pytest.raises(ValueError, match="may not exceed 512 characters"):
            iam_validators.iam_path(path)
    else:
        # Pattern: ^\/.*\/$|^\/$ (starts with /, ends with /, or is exactly /)
        iam_path_re = re.compile(r"^\/.*\/$|^\/$")
        if iam_path_re.match(path):
            result = iam_validators.iam_path(path)
            assert result == path
        else:
            with pytest.raises(ValueError, match="is not a valid iam path name"):
                iam_validators.iam_path(path)


# Test 5: AccessKey Status validation
@given(st.text())
def test_access_key_status_validation(status_value):
    """Property: status must be either 'Active' or 'Inactive'"""
    valid_statuses = ["Active", "Inactive"]
    if status_value in valid_statuses:
        result = iam_validators.status(status_value)
        assert result == status_value
    else:
        with pytest.raises(ValueError, match="Status needs to be one of"):
            iam_validators.status(status_value)


# Test 6: Required fields validation for AccessKey
@given(st.text())
def test_access_key_required_username(username):
    """Property: AccessKey requires UserName field"""
    # AccessKey has UserName as required (True)
    try:
        access_key = iam.AccessKey("TestKey", UserName=username)
        # Should succeed - verify the property was set
        assert access_key.properties["UserName"] == username
    except Exception as e:
        # Should not raise an exception for valid username
        pytest.fail(f"Unexpected exception: {e}")


# Test 7: Group class with valid names accepts them
@given(valid_iam_name_strategy())
def test_group_accepts_valid_names(name):
    """Property: Group should accept valid IAM names"""
    assume(len(name) <= 128)  # Group name limit
    try:
        group = iam.Group("TestGroup", GroupName=name)
        assert group.properties.get("GroupName") == name
    except ValueError:
        # The validator might reject it, but we expect it to work for valid names
        iam_name_re = re.compile(r"^[a-zA-Z0-9_\.\+\=\@\-\,]+$")
        if iam_name_re.match(name):
            pytest.fail(f"Valid name {name} was rejected")


# Test 8: Role class with valid names accepts them
@given(valid_iam_name_strategy())
def test_role_accepts_valid_names(name):
    """Property: Role should accept valid IAM names up to 64 chars"""
    assume(len(name) <= 64)  # Role name limit
    policy_doc = {"Version": "2012-10-17", "Statement": []}
    try:
        role = iam.Role("TestRole", 
                        RoleName=name,
                        AssumeRolePolicyDocument=policy_doc)
        assert role.properties.get("RoleName") == name
    except ValueError:
        # The validator might reject it, but we expect it to work for valid names
        iam_name_re = re.compile(r"^[a-zA-Z0-9_\.\+\=\@\-\,]+$")
        if iam_name_re.match(name):
            pytest.fail(f"Valid name {name} was rejected")


# Test 9: Valid IAM paths should be accepted
@given(st.text(alphabet="/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_", min_size=1, max_size=100))
def test_valid_iam_paths_accepted(path_content):
    """Property: Valid IAM paths should be accepted"""
    # Build a valid path
    if path_content == "/":
        path = "/"
    else:
        path = "/" + path_content + "/"
    
    assume(len(path) <= 512)
    
    result = iam_validators.iam_path(path)
    assert result == path


# Test 10: InstanceProfile requires Roles field
@given(st.lists(st.text(), min_size=1, max_size=5))
def test_instance_profile_requires_roles(roles):
    """Property: InstanceProfile requires Roles field"""
    try:
        profile = iam.InstanceProfile("TestProfile", Roles=roles)
        assert profile.properties["Roles"] == roles
    except Exception as e:
        pytest.fail(f"Failed to create InstanceProfile with required Roles: {e}")


# Test 11: ManagedPolicy requires PolicyDocument
@given(st.text())
def test_managed_policy_requires_document(description):
    """Property: ManagedPolicy requires PolicyDocument field"""
    policy_doc = {"Version": "2012-10-17", "Statement": []}
    try:
        policy = iam.ManagedPolicy("TestPolicy", 
                                   PolicyDocument=policy_doc,
                                   Description=description)
        assert policy.properties["PolicyDocument"] == policy_doc
    except Exception as e:
        pytest.fail(f"Failed to create ManagedPolicy with required PolicyDocument: {e}")