"""Property-based testing for copier.cli module."""

import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml
from hypothesis import given, strategies as st

# Add the copier environment to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._cli import _Subcommand, _handle_exceptions
from copier.errors import UserMessageError, UnsafeTemplateError


@given(st.text())
def test_data_switch_parsing_invariant(value_string: str):
    """Test that data_switch correctly handles various input strings.
    
    The help text says arguments should be of the form "VARIABLE=VALUE".
    The implementation uses split("=", 1), which should fail for strings without "=".
    """
    subcommand = _Subcommand(executable="test")
    
    # If the string contains no "=", it should raise ValueError during unpacking
    if "=" not in value_string:
        with pytest.raises(ValueError, match="not enough values to unpack"):
            subcommand.data_switch([value_string])
    else:
        # Should not raise if it contains at least one "="
        subcommand.data_switch([value_string])
        # The first part before "=" becomes the key
        key = value_string.split("=", 1)[0]
        # The rest becomes the value
        value = value_string.split("=", 1)[1]
        assert subcommand.data[key] == value


@given(st.one_of(
    st.none(),
    st.dictionaries(st.text(), st.text()),
    st.lists(st.text()),
    st.text(),
    st.integers(),
))
def test_data_file_switch_yaml_robustness(yaml_content: Any):
    """Test that data_file_switch handles various YAML content types.
    
    The implementation assumes yaml.safe_load returns a dict with .items(),
    but it can return None for empty files or other types for malformed YAML.
    """
    subcommand = _Subcommand(executable="test")
    
    # Create a temporary file with the YAML content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        if yaml_content is None:
            # Write empty file to get None from yaml.safe_load
            pass
        else:
            yaml.dump(yaml_content, f)
        temp_path = f.name
    
    try:
        # Test the method
        if not isinstance(yaml_content, dict) and yaml_content is not None:
            # Non-dict values (including None) should cause AttributeError
            with pytest.raises(AttributeError, match="'.*' object has no attribute 'items'"):
                subcommand.data_file_switch(temp_path)
        elif yaml_content is None:
            # None specifically causes AttributeError with 'NoneType'
            with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'items'"):
                subcommand.data_file_switch(temp_path)
        else:
            # Valid dict should work
            subcommand.data_file_switch(temp_path)
            # Check that data was updated (only keys not already in self.data)
            for key, value in yaml_content.items():
                if key not in subcommand.data:
                    assert key in subcommand.data
    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)


def test_handle_exceptions_return_codes():
    """Test that _handle_exceptions returns correct error codes for different exception types."""
    
    # Test UserMessageError returns 1
    def raise_user_error():
        raise UserMessageError("Test error")
    
    assert _handle_exceptions(raise_user_error) == 1
    
    # Test UnsafeTemplateError returns 0b100 (4 in decimal)
    def raise_unsafe_error():
        raise UnsafeTemplateError("Unsafe template")
    
    assert _handle_exceptions(raise_unsafe_error) == 0b100
    
    # Test successful execution returns 0
    def success():
        pass
    
    assert _handle_exceptions(success) == 0
    
    # Test KeyboardInterrupt is converted to UserMessageError with return code 1
    def raise_keyboard_interrupt():
        raise KeyboardInterrupt()
    
    assert _handle_exceptions(raise_keyboard_interrupt) == 1


@given(st.lists(st.text()))
def test_data_switch_multiple_values(values: list[str]):
    """Test that data_switch handles multiple values correctly."""
    subcommand = _Subcommand(executable="test")
    
    valid_values = []
    for v in values:
        if "=" in v:
            valid_values.append(v)
    
    if all("=" in v for v in values):
        # All values are valid
        subcommand.data_switch(values)
        for v in values:
            key, value = v.split("=", 1)
            assert subcommand.data[key] == value
    elif any("=" not in v for v in values):
        # At least one invalid value
        with pytest.raises(ValueError):
            subcommand.data_switch(values)