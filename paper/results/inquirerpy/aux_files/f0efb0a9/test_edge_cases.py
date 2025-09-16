"""Additional edge case tests for InquirerPy validators."""

import os
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
from prompt_toolkit.validation import ValidationError
import pytest
from unittest.mock import Mock

from InquirerPy.validator import (
    NumberValidator,
    PathValidator,
    EmptyInputValidator,
    PasswordValidator
)


def create_document(text):
    """Create a mock document object for validator testing."""
    doc = Mock()
    doc.text = text
    doc.cursor_position = len(text)
    return doc


# Test scientific notation and edge cases for NumberValidator
@given(st.sampled_from(['1e10', '1E10', '1.5e-10', '-1.5E+10', '3.14e0']))
def test_number_validator_scientific_notation(sci_notation):
    """NumberValidator should handle scientific notation correctly."""
    validator_float = NumberValidator(float_allowed=True)
    validator_int = NumberValidator(float_allowed=False)
    
    doc = create_document(sci_notation)
    validator_float.validate(doc)  # Should not raise
    
    # Integer validator should reject scientific notation
    with pytest.raises(ValidationError):
        validator_int.validate(doc)


@given(st.sampled_from(['inf', '-inf', 'infinity', '-infinity', 'Infinity']))
def test_number_validator_infinity_strings(inf_str):
    """Test how NumberValidator handles infinity strings."""
    validator = NumberValidator(float_allowed=True)
    doc = create_document(inf_str)
    validator.validate(doc)  # Python's float() accepts these


@given(st.sampled_from(['nan', 'NaN', 'NAN']))
def test_number_validator_nan_strings(nan_str):
    """Test how NumberValidator handles NaN strings."""
    validator = NumberValidator(float_allowed=True)
    doc = create_document(nan_str)
    validator.validate(doc)  # Python's float() accepts these


@given(st.sampled_from(['0x10', '0o10', '0b10']))
def test_number_validator_alternate_bases(num_str):
    """Test how NumberValidator handles alternate number bases."""
    validator_int = NumberValidator(float_allowed=False)
    validator_float = NumberValidator(float_allowed=True)
    
    doc = create_document(num_str)
    
    # int() accepts these formats
    validator_int.validate(doc)  # Should not raise
    
    # float() does not accept these formats
    with pytest.raises(ValidationError):
        validator_float.validate(doc)


@given(st.sampled_from(['+123', '-123', '+123.45', '-123.45', '++123', '--123']))
def test_number_validator_sign_handling(num_str):
    """Test how NumberValidator handles signs."""
    validator = NumberValidator(float_allowed=True)
    doc = create_document(num_str)
    
    if num_str.startswith('++') or num_str.startswith('--'):
        with pytest.raises(ValidationError):
            validator.validate(doc)
    else:
        validator.validate(doc)


@given(st.sampled_from(['123.', '.123', '123.0', '0.123']))
def test_number_validator_decimal_variations(num_str):
    """Test decimal point variations."""
    validator_float = NumberValidator(float_allowed=True)
    validator_int = NumberValidator(float_allowed=False)
    
    doc = create_document(num_str)
    validator_float.validate(doc)  # Should not raise
    
    with pytest.raises(ValidationError):
        validator_int.validate(doc)


# PathValidator edge cases
@given(st.sampled_from(['~', '~/test', '~root']))
def test_path_validator_tilde_expansion(path_str):
    """Test that PathValidator correctly expands tilde paths."""
    from pathlib import Path
    
    validator = PathValidator()
    doc = create_document(path_str)
    
    expanded = Path(path_str).expanduser()
    if expanded.exists():
        validator.validate(doc)
    else:
        with pytest.raises(ValidationError):
            validator.validate(doc)


def test_path_validator_symlink_handling():
    """Test how PathValidator handles symlinks."""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file and a symlink to it
        file_path = os.path.join(tmpdir, 'real_file.txt')
        link_path = os.path.join(tmpdir, 'link_to_file')
        
        with open(file_path, 'w') as f:
            f.write('test')
        
        os.symlink(file_path, link_path)
        
        # Test that symlink to file validates as file
        validator_file = PathValidator(is_file=True)
        doc = create_document(link_path)
        validator_file.validate(doc)  # Should not raise
        
        # Test that symlink to file does not validate as directory
        validator_dir = PathValidator(is_dir=True)
        with pytest.raises(ValidationError):
            validator_dir.validate(doc)


# PasswordValidator regex edge cases
def test_password_validator_regex_special_chars():
    """Test that the regex properly escapes special characters."""
    # The special chars in the code are: @$!%*#?&
    validator = PasswordValidator(special=True)
    
    # Test each special char individually
    for char in '@$!%*#?&':
        doc = create_document(char)
        validator.validate(doc)  # Should not raise
    
    # Test that other special chars don't count
    for char in '^()[]{}|\\':
        doc = create_document(char)
        with pytest.raises(ValidationError):
            validator.validate(doc)


def test_password_validator_regex_pattern_construction():
    """Test the regex pattern construction for edge cases."""
    # Test with length=0 (edge case)
    validator = PasswordValidator(length=0)
    doc = create_document('')
    validator.validate(doc)  # {0,} matches empty string
    
    # Test combined constraints with empty string
    validator = PasswordValidator(length=0, cap=True, special=True, number=True)
    doc = create_document('')
    with pytest.raises(ValidationError):
        validator.validate(doc)  # Can't have cap/special/number in empty string


@given(st.integers(min_value=-10, max_value=-1))
def test_password_validator_negative_length(negative_length):
    """Test PasswordValidator with negative length values."""
    # This is an edge case - what happens with negative length?
    validator = PasswordValidator(length=negative_length)
    
    # The regex would be .{-5,} which is invalid regex
    # Let's see if this causes an error
    doc = create_document('password')
    
    # This might raise a regex compilation error
    try:
        validator.validate(doc)
        # If it doesn't raise, the regex somehow worked
    except Exception as e:
        # Check if it's a regex error
        assert 'regex' in str(e).lower() or 'pattern' in str(e).lower()


# EmptyInputValidator edge cases
def test_empty_validator_with_null_bytes():
    """Test EmptyInputValidator with null bytes."""
    validator = EmptyInputValidator()
    
    # Null byte should count as non-empty
    doc = create_document('\0')
    validator.validate(doc)  # Should not raise
    
    # Multiple null bytes
    doc = create_document('\0\0\0')
    validator.validate(doc)  # Should not raise


@given(st.text(alphabet='\u200b\u200c\u200d\ufeff', min_size=1))
def test_empty_validator_zero_width_characters(text):
    """Test EmptyInputValidator with zero-width Unicode characters."""
    validator = EmptyInputValidator()
    doc = create_document(text)
    validator.validate(doc)  # Should not raise - they have length > 0