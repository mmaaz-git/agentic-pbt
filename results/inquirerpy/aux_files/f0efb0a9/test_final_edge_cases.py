"""Final edge case tests to probe for additional bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from prompt_toolkit.validation import ValidationError
import pytest
from unittest.mock import Mock
import re

from InquirerPy.validator import (
    NumberValidator,
    PathValidator,
    EmptyInputValidator,
    PasswordValidator
)


def create_document(text):
    doc = Mock()
    doc.text = text
    doc.cursor_position = len(text)
    return doc


# Test whitespace-only numbers
@given(st.text(alphabet=' \t\n', min_size=1, max_size=10))
def test_number_validator_whitespace_only(whitespace):
    """NumberValidator should reject whitespace-only strings."""
    validator = NumberValidator(float_allowed=True)
    doc = create_document(whitespace)
    with pytest.raises(ValidationError):
        validator.validate(doc)


# Test numbers with leading/trailing whitespace
@given(st.floats(allow_nan=False, allow_infinity=False),
       st.text(alphabet=' \t\n', min_size=1, max_size=3))
def test_number_validator_with_whitespace(num, whitespace):
    """Test if NumberValidator handles whitespace around numbers."""
    validator = NumberValidator(float_allowed=True)
    
    # Leading whitespace
    doc = create_document(whitespace + str(num))
    validator.validate(doc)  # Python's float() strips leading whitespace
    
    # Trailing whitespace
    doc = create_document(str(num) + whitespace)
    validator.validate(doc)  # Python's float() strips trailing whitespace


# Test unicode digits
def test_number_validator_unicode_digits():
    """Test if NumberValidator handles Unicode digit characters."""
    # Unicode subscript/superscript digits
    unicode_numbers = ['①②③', '₁₂₃', '¹²³']
    
    validator = NumberValidator(float_allowed=True)
    for num_str in unicode_numbers:
        doc = create_document(num_str)
        with pytest.raises(ValidationError):
            validator.validate(doc)


# Test PasswordValidator with regex metacharacters in special chars
def test_password_validator_regex_metacharacters():
    """Test if special characters are properly escaped in regex."""
    # The $ character is both a special char and a regex metachar
    validator = PasswordValidator(special=True)
    
    # Test that $ at the end doesn't break the regex
    doc = create_document("password$")
    validator.validate(doc)  # Should not raise
    
    # Test multiple $ characters
    doc = create_document("$$$")
    validator.validate(doc)  # Should not raise


# Test PathValidator with relative paths containing ..
def test_path_validator_parent_directory():
    """Test PathValidator with parent directory references."""
    import os
    
    # Get current directory and its parent
    current = os.getcwd()
    parent = os.path.dirname(current)
    
    validator = PathValidator()
    
    # Test .. (parent directory)
    doc = create_document("..")
    if os.path.exists(".."):
        validator.validate(doc)  # Should not raise
    
    # Test complex relative path
    doc = create_document("../.")
    if os.path.exists("../."):
        validator.validate(doc)  # Should not raise


# Test extreme length values for PasswordValidator
@given(st.integers(min_value=1000000, max_value=10000000))
def test_password_validator_extreme_length(huge_length):
    """Test PasswordValidator with extremely large length requirements."""
    validator = PasswordValidator(length=huge_length)
    
    # Normal password should fail
    doc = create_document("normalpassword123")
    with pytest.raises(ValidationError):
        validator.validate(doc)


# Test PasswordValidator with length=0
def test_password_validator_zero_length():
    """Test PasswordValidator with length=0."""
    validator = PasswordValidator(length=0)
    
    # Empty string should pass
    doc = create_document("")
    validator.validate(doc)  # Should not raise
    
    # Any string should pass
    doc = create_document("x")
    validator.validate(doc)  # Should not raise


# Test combining None length with other constraints
def test_password_validator_none_length_with_constraints():
    """Test PasswordValidator with None length but other constraints."""
    validator = PasswordValidator(length=None, cap=True, special=True, number=True)
    
    # Password meeting all constraints
    doc = create_document("Pass@123")
    validator.validate(doc)  # Should not raise
    
    # Empty password should fail (needs cap, special, number)
    doc = create_document("")
    with pytest.raises(ValidationError):
        validator.validate(doc)
    
    # Password missing one constraint
    doc = create_document("Pass@")  # missing number
    with pytest.raises(ValidationError):
        validator.validate(doc)


# Test malformed cursor position
def test_validators_with_bad_cursor_position():
    """Test validators when cursor_position is invalid."""
    validators = [
        NumberValidator(),
        PathValidator(),
        EmptyInputValidator(),
        PasswordValidator()
    ]
    
    doc = Mock()
    doc.text = "test"
    doc.cursor_position = -1  # Invalid cursor position
    
    # Validators should still work - they don't use cursor_position for validation
    for validator in validators[:-1]:
        try:
            validator.validate(doc)
        except ValidationError:
            pass  # Expected for some validators
        except Exception as e:
            # Unexpected error related to cursor position
            pytest.fail(f"Unexpected error with cursor_position=-1: {e}")


# Test custom error messages
def test_custom_error_messages():
    """Test that custom error messages are properly used."""
    custom_msg = "Custom error message with special chars: $@!%"
    
    validators = [
        NumberValidator(message=custom_msg),
        PathValidator(message=custom_msg),
        EmptyInputValidator(message=custom_msg),
        PasswordValidator(message=custom_msg)
    ]
    
    invalid_inputs = ["not_a_number", "/nonexistent/path", "", "weak"]
    
    for validator, invalid_input in zip(validators, invalid_inputs):
        doc = create_document(invalid_input)
        try:
            validator.validate(doc)
        except ValidationError as e:
            assert e.message == custom_msg, f"Expected custom message, got: {e.message}"