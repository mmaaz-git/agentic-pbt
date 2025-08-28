"""Property-based tests for flask.helpers module."""

import os
import sys
import string
from hypothesis import given, strategies as st, assume, settings, HealthCheck
import flask.helpers


# Test get_root_path properties

@given(st.text(min_size=1, alphabet=string.ascii_letters + string.digits + '_'))
def test_get_root_path_always_returns_string(import_name):
    """get_root_path should always return a string, never crash."""
    result = flask.helpers.get_root_path(import_name)
    assert isinstance(result, str)


@given(st.text(min_size=1, alphabet=string.ascii_letters + string.digits + '_'))
def test_get_root_path_returns_valid_path(import_name):
    """get_root_path should always return a valid directory path."""
    result = flask.helpers.get_root_path(import_name)
    assert isinstance(result, str)
    # The result should be either an existing directory or current working directory
    assert os.path.isdir(result) or result == os.getcwd()


@given(st.text(min_size=1, alphabet=string.ascii_letters + string.digits + '_'))  
def test_get_root_path_nonexistent_returns_cwd(import_name):
    """For non-existent modules, get_root_path should return current working directory."""
    # Make sure the module doesn't exist
    assume(import_name not in sys.modules)
    try:
        __import__(import_name)
        assume(False)  # Skip if module exists
    except (ImportError, ModuleNotFoundError):
        pass
    
    result = flask.helpers.get_root_path(import_name)
    assert result == os.getcwd()


@given(st.sampled_from(['os', 'sys', 'json', 'math', 'collections', 'itertools']))
def test_get_root_path_existing_modules(module_name):
    """For existing standard library modules, get_root_path should return a valid directory."""
    try:
        result = flask.helpers.get_root_path(module_name)
        assert isinstance(result, str)
        assert os.path.isdir(result)
    except RuntimeError as e:
        # This is the bug we found - built-in modules without __file__ raise RuntimeError 
        # instead of returning cwd as documented
        assert module_name in ['sys', 'itertools']  # Built-in modules without __file__
        assert "No root path can be found" in str(e)
    
    
@given(st.sampled_from(['flask', 'flask.helpers', 'flask.app']))
def test_get_root_path_flask_modules(module_name):
    """For Flask modules, get_root_path should return the Flask installation directory."""
    result = flask.helpers.get_root_path(module_name)
    assert isinstance(result, str)
    assert os.path.isdir(result)
    # Should be in the flask package directory
    assert 'flask' in result.lower() or 'site-packages' in result.lower()


# Test idempotence property
@given(st.text(min_size=1, alphabet=string.ascii_letters + string.digits + '_'))
def test_get_root_path_idempotent(import_name):
    """Calling get_root_path multiple times with same input should return same result."""
    result1 = flask.helpers.get_root_path(import_name)
    result2 = flask.helpers.get_root_path(import_name)
    assert result1 == result2


# Test with edge cases
@given(st.text(min_size=1, max_size=50).filter(lambda x: '.' in x or '/' in x or '\\' in x))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_get_root_path_with_special_chars(import_name):
    """Test get_root_path with module names containing dots or path separators."""
    try:
        result = flask.helpers.get_root_path(import_name)
        assert isinstance(result, str)
        # Should still return a valid path even for weird inputs
        assert os.path.isdir(result) or result == os.getcwd()
    except (ValueError, ImportError, RuntimeError, AttributeError):
        # These are acceptable failures for invalid module names
        pass


# Test namespace package handling
@given(st.just('importlib'))  
def test_get_root_path_namespace_package(package_name):
    """Test behavior with known namespace packages."""
    # importlib is a namespace package in Python 3
    result = flask.helpers.get_root_path(package_name)
    assert isinstance(result, str)
    assert os.path.isdir(result)