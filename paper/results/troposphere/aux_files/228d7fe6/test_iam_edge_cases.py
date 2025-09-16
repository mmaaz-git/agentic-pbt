#!/usr/bin/env python3
"""Edge case property-based tests for troposphere.iam module."""

import re
from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the targets
from troposphere import iam
from troposphere.validators import iam as iam_validators


# Test for potential bug in error message
@given(st.text(min_size=129, max_size=200))
def test_iam_group_name_error_message_bug(name):
    """Check if error message for group name says 'Role Name' instead of 'Group Name'"""
    # The group validator checks > 128 but the error says "IAM Role Name"
    with pytest.raises(ValueError) as exc_info:
        iam_validators.iam_group_name(name)
    
    error_msg = str(exc_info.value)
    # BUG: The error message says "IAM Role Name" but this is for group names!
    assert "IAM Role Name may not exceed 128 characters" in error_msg


# Test path validation edge cases
@given(st.text())
def test_iam_path_edge_cases(path):
    """Test edge cases in IAM path validation"""
    # The regex is: ^\/.*\/$|^\/$
    # This means: starts with /, ends with /, OR is exactly /
    
    if len(path) > 512:
        with pytest.raises(ValueError):
            iam_validators.iam_path(path)
        return
    
    # Test some specific patterns
    if path == "/":
        # Single slash should be valid
        result = iam_validators.iam_path(path)
        assert result == path
    elif path.startswith("/") and path.endswith("/") and len(path) > 1:
        # Should be valid
        result = iam_validators.iam_path(path)
        assert result == path
    elif not (path.startswith("/") and path.endswith("/")):
        # Should be invalid
        with pytest.raises(ValueError, match="is not a valid iam path name"):
            iam_validators.iam_path(path)


# Test for format string bug in iam_path
@given(st.text(min_size=513, max_size=600))
def test_iam_path_format_string_bug(path):
    """Test if iam_path has a format string bug in error message"""
    with pytest.raises(ValueError) as exc_info:
        iam_validators.iam_path(path)
    
    error_msg = str(exc_info.value)
    # Check if the path is properly formatted in the error message
    # The code has: raise ValueError("IAM path %s may not exceed 512 characters", path)
    # This is WRONG - it should use % formatting or .format()
    # It will create a tuple instead of formatting the string
    assert isinstance(exc_info.value.args, tuple) and len(exc_info.value.args) == 2


# Test user name error message formatting
@given(st.text(min_size=65, max_size=100))
def test_iam_user_name_error_format_bug(name):
    """Test if user name validator has format string bug"""
    with pytest.raises(ValueError) as exc_info:
        iam_validators.iam_user_name(name)
    
    # The error message should properly format the string
    error_msg = str(exc_info.value)
    assert "may not exceed 64 characters" in error_msg


# Test another format string issue
@given(st.text())
def test_iam_user_name_invalid_format_bug(name):
    """Test format string in invalid user name error"""
    assume(name and len(name) <= 64)
    # Use a name that doesn't match the regex
    assume(not re.match(r"^[\w+=,.@-]+$", name))
    
    with pytest.raises(ValueError) as exc_info:
        iam_validators.iam_user_name(name)
    
    # Check the error format - code has:
    # raise ValueError("%s is not a valid value for AWS::IAM::User property 'UserName'", user_name)
    # This is WRONG format - should be % user_name or .format(user_name)
    assert isinstance(exc_info.value.args, tuple) and len(exc_info.value.args) == 2


# Test IAM names validator directly
@given(st.text())  
def test_iam_names_validator(name):
    """Test the generic iam_names validator"""
    iam_name_re = re.compile(r"^[a-zA-Z0-9_\.\+\=\@\-\,]+$")
    
    if iam_name_re.match(name):
        result = iam_validators.iam_names(name)
        assert result == name
    else:
        with pytest.raises(ValueError, match="is not a valid iam name"):
            iam_validators.iam_names(name)


# Test empty string handling
def test_empty_strings():
    """Test how validators handle empty strings"""
    
    # Empty group name - should fail on regex
    with pytest.raises(ValueError, match="is not a valid iam name"):
        iam_validators.iam_group_name("")
    
    # Empty role name - should fail on regex
    with pytest.raises(ValueError, match="is not a valid iam name"):
        iam_validators.iam_role_name("")
    
    # Empty user name - has specific check
    with pytest.raises(ValueError, match="may not be empty"):
        iam_validators.iam_user_name("")
    
    # Empty path - should fail on regex
    with pytest.raises(ValueError, match="is not a valid iam path name"):
        iam_validators.iam_path("")


# Test boundary values for lengths
def test_length_boundaries():
    """Test exact boundary values for length constraints"""
    
    # Group name at exactly 128 characters (should pass)
    name_128 = "a" * 128
    result = iam_validators.iam_group_name(name_128)
    assert result == name_128
    
    # Group name at 129 characters (should fail)
    name_129 = "a" * 129
    with pytest.raises(ValueError, match="IAM Role Name may not exceed 128 characters"):
        iam_validators.iam_group_name(name_129)
    
    # Role name at exactly 64 characters (should pass)
    name_64 = "a" * 64
    result = iam_validators.iam_role_name(name_64)
    assert result == name_64
    
    # Role name at 65 characters (should fail)
    name_65 = "a" * 65
    with pytest.raises(ValueError, match="IAM Role Name may not exceed 64 characters"):
        iam_validators.iam_role_name(name_65)
    
    # User name at exactly 64 characters (should pass)
    result = iam_validators.iam_user_name(name_64)
    assert result == name_64
    
    # User name at 65 characters (should fail)
    with pytest.raises(ValueError, match="may not exceed 64 characters"):
        iam_validators.iam_user_name(name_65)
    
    # Path at exactly 512 characters (should pass if valid format)
    path_510 = "/" + "a" * 510 + "/"  # Total 512
    result = iam_validators.iam_path(path_510)
    assert result == path_510
    
    # Path at 513 characters (should fail)
    path_513 = "/" + "a" * 511 + "/"  # Total 513
    with pytest.raises(ValueError) as exc_info:
        iam_validators.iam_path(path_513)
    # Check for format string bug
    assert isinstance(exc_info.value.args, tuple) and len(exc_info.value.args) == 2