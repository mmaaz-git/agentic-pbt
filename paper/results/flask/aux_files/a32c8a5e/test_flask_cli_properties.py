"""Property-based tests for flask.cli module"""

import ast
import os
import sys
import tempfile
from unittest.mock import Mock
from hypothesis import given, strategies as st, assume, settings
import flask.cli
from flask import Flask


# Strategy for valid Python identifiers
valid_python_identifiers = st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True)

# Strategy for simple literals that ast.literal_eval can handle
simple_literals = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=100)
)


@given(valid_python_identifiers)
def test_find_app_by_string_valid_names(name):
    """Test that valid Python identifiers are parsed correctly"""
    # Create a mock module with the attribute
    module = Mock()
    app = Flask(__name__)
    setattr(module, name, app)
    module.__name__ = "test_module"
    
    # Should successfully find and return the app
    result = flask.cli.find_app_by_string(module, name)
    assert result is app


@given(valid_python_identifiers, st.lists(simple_literals, min_size=0, max_size=3))
def test_find_app_by_string_function_calls(func_name, args):
    """Test that function calls with literal arguments are parsed correctly"""
    # Create a mock module with a function
    module = Mock()
    app = Flask(__name__)
    
    def factory(*a, **kw):
        return app
    
    setattr(module, func_name, factory)
    module.__name__ = "test_module"
    
    # Build the function call string
    args_str = ", ".join(repr(arg) for arg in args)
    call_str = f"{func_name}({args_str})"
    
    # Should successfully call the function and return the app
    result = flask.cli.find_app_by_string(module, call_str)
    assert result is app


@given(st.text(min_size=1))
def test_find_app_by_string_invalid_syntax(text):
    """Test that invalid Python syntax is rejected properly"""
    module = Mock()
    module.__name__ = "test_module"
    
    # Check if it's valid Python expression first
    try:
        ast.parse(text.strip(), mode="eval")
        # If it parses, it might be valid - skip this test case
        return
    except SyntaxError:
        # Invalid syntax - should raise NoAppException
        try:
            flask.cli.find_app_by_string(module, text)
            assert False, f"Expected NoAppException for invalid syntax: {text!r}"
        except flask.cli.NoAppException as e:
            # Expected - check error message mentions parsing
            assert "Failed to parse" in str(e) or "attribute name" in str(e)


@given(st.lists(st.text(min_size=0, max_size=50), min_size=0, max_size=5))
def test_separated_path_type_split_join_roundtrip(paths):
    """Test that splitting and joining paths is a round-trip operation"""
    # Filter out paths with the separator to avoid ambiguity
    paths = [p for p in paths if os.pathsep not in p]
    
    # Join paths with OS separator
    joined = os.pathsep.join(paths)
    
    # Create SeparatedPathType and test split
    sep_type = flask.cli.SeparatedPathType()
    split_result = sep_type.split_envvar_value(joined)
    
    # Should get back the original paths
    assert list(split_result) == paths


@given(st.text())
def test_separated_path_type_empty_handling(text):
    """Test edge cases in path splitting"""
    sep_type = flask.cli.SeparatedPathType()
    result = sep_type.split_envvar_value(text)
    
    # Result should always be a sequence
    assert isinstance(result, list)
    
    # Empty input should give single empty string
    if not text:
        assert result == [""]
    
    # Count of separators should match splits
    separator_count = text.count(os.pathsep)
    assert len(result) == separator_count + 1


@given(st.text(min_size=0))
def test_prepare_import_strips_py_extension(filename):
    """Test that prepare_import correctly handles .py extensions"""
    # Skip if filename contains null bytes or other problematic chars
    assume('\x00' not in filename)
    assume(not filename.startswith('/'))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        if filename and filename != '.':
            test_path = os.path.join(tmpdir, filename)
            
            # Handle edge cases with path creation
            try:
                # Ensure parent directory exists
                parent = os.path.dirname(test_path)
                if parent and parent != tmpdir:
                    os.makedirs(parent, exist_ok=True)
                
                # Create the file with .py extension
                if not test_path.endswith('.py'):
                    test_path = test_path + '.py'
                
                with open(test_path, 'w') as f:
                    f.write("# test file")
                
                # Call prepare_import
                result = flask.cli.prepare_import(test_path)
                
                # Result should not end with .py
                assert not result.endswith('.py'), f"Result {result!r} should not end with .py"
                
                # If path had .py extension, it should be stripped
                if test_path.endswith('.py'):
                    base_name = os.path.basename(test_path[:-3])
                    assert base_name in result or result == base_name
            except (OSError, ValueError):
                # Skip invalid paths
                pass


@given(valid_python_identifiers, valid_python_identifiers)  
def test_find_app_by_string_attribute_access(module_attr, app_attr):
    """Test accessing nested attributes (currently not supported but interesting)"""
    module = Mock()
    module.__name__ = "test_module"
    
    # Test that dotted names are not supported (based on source analysis)
    dotted_name = f"{module_attr}.{app_attr}"
    
    try:
        flask.cli.find_app_by_string(module, dotted_name)
        # If this succeeds, it means the function parsed it somehow
    except flask.cli.NoAppException as e:
        # Expected - dotted names should fail parsing
        assert "Failed to parse" in str(e) or "attribute name" in str(e)
    except SyntaxError:
        # Also acceptable - invalid syntax
        pass