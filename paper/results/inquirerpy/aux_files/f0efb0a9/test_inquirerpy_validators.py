"""Property-based tests for InquirerPy validators using Hypothesis."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock

from hypothesis import assume, given, strategies as st
import pytest

# Import from the installed InquirerPy in the virtual environment
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from prompt_toolkit.validation import ValidationError
from InquirerPy.validator import (
    NumberValidator,
    PathValidator,
    EmptyInputValidator,
    PasswordValidator
)


# Helper to create a mock document
def create_document(text):
    """Create a mock document object for validator testing."""
    doc = Mock()
    doc.text = text
    doc.cursor_position = len(text)
    return doc


# Test NumberValidator
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_number_validator_float_allowed_accepts_floats(value):
    """When float_allowed=True, the validator should accept float values."""
    validator = NumberValidator(float_allowed=True)
    doc = create_document(str(value))
    validator.validate(doc)  # Should not raise


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_number_validator_float_not_allowed_rejects_floats(value):
    """When float_allowed=False, the validator should reject non-integer float values."""
    assume(value != int(value))  # Only test non-integer floats
    validator = NumberValidator(float_allowed=False)
    doc = create_document(str(value))
    with pytest.raises(ValidationError):
        validator.validate(doc)


@given(st.integers())
def test_number_validator_accepts_integers_regardless_of_float_setting(value):
    """Integer values should be accepted regardless of float_allowed setting."""
    validator_no_float = NumberValidator(float_allowed=False)
    validator_float = NumberValidator(float_allowed=True)
    
    doc = create_document(str(value))
    validator_no_float.validate(doc)  # Should not raise
    validator_float.validate(doc)  # Should not raise


@given(st.text(min_size=1).filter(lambda x: not x.strip().replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '').isdigit()))
def test_number_validator_rejects_non_numeric_strings(text):
    """Non-numeric strings should be rejected by NumberValidator."""
    # Filter out strings that could be valid numbers
    try:
        float(text)
        assume(False)  # Skip if it's actually a valid number
    except ValueError:
        pass  # This is what we want - a non-numeric string
    
    validator = NumberValidator(float_allowed=True)
    doc = create_document(text)
    with pytest.raises(ValidationError):
        validator.validate(doc)


# Test PathValidator
def test_path_validator_file_and_dir_mutual_exclusivity():
    """A path cannot be both a file and a directory simultaneously."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_path = tmp_file.name
        
    try:
        # This path is a file, not a directory
        validator = PathValidator(is_file=True, is_dir=True)
        doc = create_document(tmp_path)
        
        # Should raise because path cannot be both file and dir
        with pytest.raises(ValidationError):
            validator.validate(doc)
            
    finally:
        os.unlink(tmp_path)


def test_path_validator_directory_validation():
    """Test directory validation works correctly."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        validator_dir = PathValidator(is_dir=True)
        validator_file = PathValidator(is_file=True)
        
        doc = create_document(tmp_dir)
        
        # Should pass for is_dir=True
        validator_dir.validate(doc)
        
        # Should fail for is_file=True
        with pytest.raises(ValidationError):
            validator_file.validate(doc)


@given(st.text(min_size=1))
def test_path_validator_nonexistent_paths(path_str):
    """Non-existent paths should fail validation."""
    # Create a path that definitely doesn't exist
    non_existent = f"/tmp/nonexistent_{hash(path_str)}_{os.getpid()}/test.txt"
    assume(not Path(non_existent).exists())
    
    validator = PathValidator()
    doc = create_document(non_existent)
    
    with pytest.raises(ValidationError):
        validator.validate(doc)


# Test EmptyInputValidator
@given(st.text(min_size=1))
def test_empty_validator_accepts_non_empty(text):
    """EmptyInputValidator should accept any non-empty string."""
    validator = EmptyInputValidator()
    doc = create_document(text)
    validator.validate(doc)  # Should not raise


def test_empty_validator_rejects_empty():
    """EmptyInputValidator should reject empty strings."""
    validator = EmptyInputValidator()
    doc = create_document("")
    
    with pytest.raises(ValidationError):
        validator.validate(doc)


@given(st.text(alphabet=' \t\n\r', min_size=1))
def test_empty_validator_accepts_whitespace(whitespace):
    """EmptyInputValidator should accept whitespace-only strings (based on len() > 0 check)."""
    validator = EmptyInputValidator()
    doc = create_document(whitespace)
    validator.validate(doc)  # Should not raise because len(whitespace) > 0


# Test PasswordValidator
@given(st.text(min_size=1))
def test_password_validator_no_constraints_accepts_any_text(text):
    """PasswordValidator with no constraints should accept any non-empty text."""
    validator = PasswordValidator()
    doc = create_document(text)
    validator.validate(doc)  # Should not raise


@given(st.integers(min_value=1, max_value=20), st.text(min_size=0, max_size=30))
def test_password_validator_length_constraint(min_length, password):
    """PasswordValidator should enforce minimum length when specified."""
    validator = PasswordValidator(length=min_length)
    doc = create_document(password)
    
    if len(password) >= min_length:
        validator.validate(doc)  # Should not raise
    else:
        with pytest.raises(ValidationError):
            validator.validate(doc)


@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789!@#$%', min_size=1))
def test_password_validator_capital_constraint(password):
    """PasswordValidator should enforce capital letter requirement when specified."""
    validator = PasswordValidator(cap=True)
    doc = create_document(password)
    
    has_capital = any(c.isupper() for c in password)
    
    if has_capital:
        validator.validate(doc)
    else:
        with pytest.raises(ValidationError):
            validator.validate(doc)


@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1))
def test_password_validator_special_char_constraint(password):
    """PasswordValidator should enforce special character requirement when specified."""
    validator = PasswordValidator(special=True)
    doc = create_document(password)
    
    special_chars = '@$!%*#?&'
    has_special = any(c in special_chars for c in password)
    
    if has_special:
        validator.validate(doc)
    else:
        with pytest.raises(ValidationError):
            validator.validate(doc)


@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%', min_size=1))
def test_password_validator_number_constraint(password):
    """PasswordValidator should enforce number requirement when specified."""
    validator = PasswordValidator(number=True)
    doc = create_document(password)
    
    has_number = any(c.isdigit() for c in password)
    
    if has_number:
        validator.validate(doc)
    else:
        with pytest.raises(ValidationError):
            validator.validate(doc)


@given(
    st.integers(min_value=1, max_value=10),
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.text(min_size=0, max_size=20)
)
def test_password_validator_combined_constraints(length, cap, special, number, password):
    """Test PasswordValidator with multiple constraints combined."""
    validator = PasswordValidator(length=length, cap=cap, special=special, number=number)
    doc = create_document(password)
    
    # Check all constraints
    meets_length = len(password) >= length
    meets_cap = not cap or any(c.isupper() for c in password)
    meets_special = not special or any(c in '@$!%*#?&' for c in password)
    meets_number = not number or any(c.isdigit() for c in password)
    
    if meets_length and meets_cap and meets_special and meets_number:
        validator.validate(doc)
    else:
        with pytest.raises(ValidationError):
            validator.validate(doc)


# Test for edge cases and potential bugs
def test_password_validator_empty_string_with_no_length():
    """Empty password should be accepted when no length constraint is specified."""
    validator = PasswordValidator()
    doc = create_document("")
    validator.validate(doc)  # Based on regex .* which matches empty string


def test_password_validator_empty_string_with_constraints():
    """Empty password should fail when constraints are specified."""
    validator = PasswordValidator(cap=True)
    doc = create_document("")
    with pytest.raises(ValidationError):
        validator.validate(doc)