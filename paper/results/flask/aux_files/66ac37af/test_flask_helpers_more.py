"""Additional property-based tests for flask.helpers module."""

import os
import sys
import string
from hypothesis import given, strategies as st, assume, settings, HealthCheck
import flask.helpers


# Test edge cases for get_root_path with empty strings and special module names
@given(st.just(''))
def test_get_root_path_empty_string(import_name):
    """Test get_root_path with empty string - should handle gracefully."""
    try:
        result = flask.helpers.get_root_path(import_name)
        # If it doesn't crash, should return a valid path
        assert isinstance(result, str)
        assert os.path.isdir(result) or result == os.getcwd()
    except (ValueError, ImportError, RuntimeError, ModuleNotFoundError):
        # These are acceptable failures for invalid input
        pass


# Test with __main__ module
@given(st.just('__main__'))
def test_get_root_path_main_module(import_name):
    """Test get_root_path with __main__ module."""
    result = flask.helpers.get_root_path(import_name)
    assert isinstance(result, str)
    # Should return current working directory for __main__ in most cases
    assert os.path.isdir(result)


# Test modules with dots (packages)
@given(st.sampled_from(['email.mime', 'urllib.parse', 'xml.etree', 'http.client']))
def test_get_root_path_dotted_modules(module_name):
    """Test get_root_path with dotted module names (submodules)."""
    result = flask.helpers.get_root_path(module_name)
    assert isinstance(result, str)
    assert os.path.isdir(result)


# Test with module names that might cause path traversal issues
@settings(suppress_health_check=[HealthCheck.filter_too_much])
@given(st.text(min_size=1).filter(lambda x: '..' in x or '../' in x))
def test_get_root_path_path_traversal(import_name):
    """Test get_root_path doesn't allow path traversal attacks."""
    try:
        result = flask.helpers.get_root_path(import_name)
        # If successful, should still return a safe path
        assert isinstance(result, str)
        # Should not contain path traversal patterns in the result
        assert '../' not in result  
    except (ValueError, ImportError, RuntimeError, ModuleNotFoundError, AttributeError):
        # Expected to fail for invalid module names
        pass


# Test with Unicode module names
@given(st.text(alphabet='αβγδεζηθικλμνξοπρστυφχψω', min_size=1, max_size=10))
def test_get_root_path_unicode(import_name):
    """Test get_root_path with Unicode characters."""
    try:
        result = flask.helpers.get_root_path(import_name)
        assert isinstance(result, str)
        assert os.path.isdir(result) or result == os.getcwd()
    except (ValueError, ImportError, RuntimeError, ModuleNotFoundError, SyntaxError):
        # Expected to fail for non-ASCII module names
        pass


# Test module names with numbers
@given(st.text(alphabet=string.digits, min_size=1, max_size=10))
def test_get_root_path_numeric_only(import_name):
    """Test get_root_path with numeric-only module names."""
    try:
        result = flask.helpers.get_root_path(import_name)
        assert isinstance(result, str)
        assert os.path.isdir(result) or result == os.getcwd()
    except (ValueError, ImportError, RuntimeError, ModuleNotFoundError, SyntaxError):
        # Module names starting with numbers are invalid in Python
        pass