import os
import sys
import importlib
import pathlib
from hypothesis import given, strategies as st, assume, settings
import flask.sansio.app
import flask.sansio.scaffold


# Strategy for valid Python module names
def valid_module_name():
    # Start with letter or underscore, then letters, digits, underscores
    first_char = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_', min_size=1, max_size=1)
    rest_chars = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_', min_size=0, max_size=20)
    return st.builds(lambda f, r: f + r, first_char, rest_chars)

# Strategy for dotted module names
dotted_module_name = st.lists(valid_module_name(), min_size=1, max_size=5).map(lambda x: '.'.join(x))

# Strategy for existing module names (limited to avoid import side effects)
existing_modules = st.sampled_from(['os', 'sys', 'json', 'math', 'collections', 'itertools', 'functools'])


@given(dotted_module_name)
@settings(max_examples=100)
def test_find_package_path_always_returns_string(import_name):
    """_find_package_path should always return a string path, never None."""
    result = flask.sansio.scaffold._find_package_path(import_name)
    assert isinstance(result, str), f"Expected string, got {type(result)}"
    # The path should be an absolute path
    assert os.path.isabs(result), f"Expected absolute path, got {result}"


@given(dotted_module_name)
@settings(max_examples=100)  
def test_find_package_path_fallback_to_cwd(import_name):
    """_find_package_path should fall back to current working directory for non-existent modules."""
    # Skip if this happens to be a real module
    try:
        spec = importlib.util.find_spec(import_name.split('.')[0])
        if spec is not None:
            assume(False)
    except (ImportError, ValueError):
        pass
    
    result = flask.sansio.scaffold._find_package_path(import_name)
    expected = os.getcwd()
    assert result == expected, f"Expected {expected}, got {result}"


@given(existing_modules)
@settings(max_examples=50)
def test_get_root_path_consistency_for_imported_modules(module_name):
    """get_root_path should return the same path consistently for already imported modules."""
    # Import the module first
    __import__(module_name)
    
    # Call get_root_path multiple times
    result1 = flask.sansio.scaffold.get_root_path(module_name)
    result2 = flask.sansio.scaffold.get_root_path(module_name)
    
    assert result1 == result2, f"Inconsistent results: {result1} != {result2}"
    assert os.path.exists(result1), f"Path does not exist: {result1}"


@given(dotted_module_name)
@settings(max_examples=100)
def test_find_package_returns_tuple(import_name):
    """find_package should always return a tuple of (prefix or None, path)."""
    prefix, path = flask.sansio.app.find_package(import_name)
    
    # prefix can be None or a string
    assert prefix is None or isinstance(prefix, str), f"Prefix must be None or string, got {type(prefix)}"
    
    # path must always be a string
    assert isinstance(path, str), f"Path must be string, got {type(path)}"
    
    # If prefix is not None, it should be an absolute path
    if prefix is not None:
        assert os.path.isabs(prefix), f"Prefix should be absolute path: {prefix}"


@given(existing_modules)
@settings(max_examples=50)
def test_find_package_consistency(module_name):
    """find_package should return consistent results for the same input."""
    result1 = flask.sansio.app.find_package(module_name)
    result2 = flask.sansio.app.find_package(module_name)
    
    assert result1 == result2, f"Inconsistent results: {result1} != {result2}"


@given(existing_modules)
@settings(max_examples=50)
def test_find_package_and_find_package_path_relationship(module_name):
    """The path from find_package should be related to _find_package_path result."""
    prefix, package_path = flask.sansio.app.find_package(module_name)
    find_path_result = flask.sansio.scaffold._find_package_path(module_name)
    
    # The package_path from find_package should be the same as _find_package_path
    assert package_path == find_path_result, f"Path mismatch: {package_path} != {find_path_result}"


@given(dotted_module_name)
@settings(max_examples=100)
def test_find_package_prefix_path_relationship(import_name):
    """If find_package returns a prefix, the path should be under that prefix."""
    prefix, path = flask.sansio.app.find_package(import_name)
    
    if prefix is not None and prefix != '' and path != '':
        # Convert to PurePath for reliable path comparison
        prefix_path = pathlib.PurePath(os.path.abspath(prefix))
        package_path = pathlib.PurePath(os.path.abspath(path))
        
        # The package path should be relative to the prefix for installed packages
        # But this is only true for packages in site-packages
        if 'site-packages' in str(package_path):
            # Check if package_path starts with prefix_path
            try:
                package_path.relative_to(prefix_path)
                path_is_under_prefix = True
            except ValueError:
                path_is_under_prefix = False
            
            assert path_is_under_prefix, f"Path {path} is not under prefix {prefix}"


@given(st.text(min_size=1, max_size=100))
@settings(max_examples=200)
def test_find_package_no_crash_on_arbitrary_input(import_name):
    """find_package should not crash on arbitrary string input."""
    try:
        prefix, path = flask.sansio.app.find_package(import_name)
        # If it returns, it should return valid types
        assert prefix is None or isinstance(prefix, str)
        assert isinstance(path, str)
    except (ImportError, ValueError, AttributeError):
        # These exceptions are acceptable for invalid module names
        pass


@given(st.text(min_size=1, max_size=100))
@settings(max_examples=200)
def test_find_package_path_no_crash_on_arbitrary_input(import_name):
    """_find_package_path should not crash on arbitrary string input."""
    try:
        result = flask.sansio.scaffold._find_package_path(import_name)
        # Should always return a string
        assert isinstance(result, str)
    except (ImportError, ValueError, AttributeError):
        # These exceptions are acceptable for invalid module names
        pass