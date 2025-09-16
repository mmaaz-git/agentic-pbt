#!/usr/bin/env python3
"""Property-based tests for the Python Fire library."""

import ast
import json
import sys
import os

# Add the fire_env site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

import fire
from fire import parser
from fire import value_types
from fire import core
from hypothesis import given, strategies as st, assume, settings, example
import pytest
import math


# Test 1: DefaultParseValue should correctly parse Python literals
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
    st.text().filter(lambda x: x not in ('True', 'False', 'None')),  # Strings that aren't Python keywords
    st.lists(st.integers(), max_size=10),
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=10),
    st.tuples(st.integers(), st.text()),
))
def test_default_parse_value_literals(value):
    """Test that DefaultParseValue correctly handles Python literals."""
    # Convert the value to a string representation
    if isinstance(value, str):
        # Regular strings should be returned as-is when they can't be parsed as literals
        str_repr = value
    else:
        str_repr = repr(value)
    
    result = parser.DefaultParseValue(str_repr)
    
    # The function should either parse it as a Python value or return it as a string
    if isinstance(value, str):
        # Non-literal strings should be returned as strings
        assert isinstance(result, str)
    else:
        # Literals should be parsed to their Python values
        assert result == value


# Test 2: YAML-like dict syntax parsing
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        st.one_of(st.integers(), st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))),
        min_size=1,
        max_size=5
    )
)
def test_yaml_like_dict_parsing(d):
    """Test that Fire can parse YAML-like dict syntax {a: b}."""
    # Create YAML-like syntax
    items = []
    for key, value in d.items():
        if isinstance(value, str):
            items.append(f"{key}: {value}")
        else:
            items.append(f"{key}: {value}")
    yaml_like = "{" + ", ".join(items) + "}"
    
    result = parser.DefaultParseValue(yaml_like)
    
    # The result should be a dict with string keys
    assert isinstance(result, dict)
    # Keys should match (all become strings in YAML-like syntax)
    assert set(result.keys()) == set(d.keys())


# Test 3: SeparateFlagArgs should correctly split on '--'
@given(
    st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=20)
)
def test_separate_flag_args_invariant(args):
    """Test that SeparateFlagArgs correctly splits arguments on '--'."""
    # Insert '--' at various positions
    if '--' in args:
        fire_args, flag_args = parser.SeparateFlagArgs(args)
        
        # The combined result should reconstruct the original (minus the separator)
        if flag_args:
            # Find the last occurrence of '--'
            separator_indices = [i for i, arg in enumerate(args) if arg == '--']
            last_separator = separator_indices[-1]
            
            # Check that fire_args matches everything before the last '--'
            assert fire_args == args[:last_separator]
            # Check that flag_args matches everything after the last '--'
            assert flag_args == args[last_separator + 1:]
    else:
        fire_args, flag_args = parser.SeparateFlagArgs(args)
        # Without '--', all args should be fire args
        assert fire_args == args
        assert flag_args == []


# Test 4: Round-trip property for simple values through _OneLineResult
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
    st.text(),
    st.lists(st.integers(), max_size=10),
    st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), max_size=5),
))
def test_one_line_result_serialization(value):
    """Test that _OneLineResult produces valid single-line output."""
    result = core._OneLineResult(value)
    
    # Result should be a string
    assert isinstance(result, str)
    
    # Result should not contain newlines (single line property)
    assert '\n' not in result
    
    # For JSON-serializable values, we should be able to parse them back
    if isinstance(value, (int, float, bool, type(None), list, dict)) and value is not None:
        try:
            if isinstance(value, (list, dict)):
                # JSON dumps should work
                parsed = json.loads(result)
                assert parsed == value
        except (json.JSONDecodeError, TypeError, ValueError):
            # Some values might be stringified instead
            pass


# Test 5: Value type categorization should be mutually exclusive
@given(st.one_of(
    st.integers(),
    st.floats(),
    st.text(),
    st.booleans(),
    st.none(),
    st.functions(),
    st.sampled_from([int, str, list, dict]),  # Classes
))
def test_value_type_categorization(component):
    """Test that value type categorization functions are consistent."""
    is_value = value_types.IsValue(component)
    is_command = value_types.IsCommand(component)
    is_group = value_types.IsGroup(component)
    
    # A component can't be both a value and a command
    if is_value:
        assert not is_command
    
    # A command can't be a value
    if is_command:
        assert not is_value
        assert not is_group
    
    # Exactly one should be true for most cases
    # (Groups are things that aren't values or commands)


# Test 6: Special case handling in parser
@given(st.text())
def test_parser_comment_handling(text):
    """Test that parser handles comments correctly."""
    # If the text contains '#', it might be treated as a comment
    if '#' in text and not (text.startswith('"') or text.startswith("'")):
        # Test that comments are handled
        try:
            result = parser.DefaultParseValue(text)
            # If it succeeds, the result should be a string (not parsed)
            assert isinstance(result, str)
        except (SyntaxError, ValueError):
            # Comments might cause syntax errors
            pass


# Test 7: Edge cases in YAML-like syntax
@given(st.text(min_size=1, max_size=20))
@example("{}")
@example("{a:}")
@example("{:b}")
@example("{a:b:c}")
def test_yaml_edge_cases(text):
    """Test edge cases in YAML-like dict parsing."""
    if text.startswith('{') and text.endswith('}'):
        try:
            result = parser.DefaultParseValue(text)
            # Should either parse as dict or return as string
            assert isinstance(result, (dict, str))
        except (SyntaxError, ValueError):
            # Invalid syntax should raise an error
            pass


# Test 8: Testing the Fire main function with various components
@given(st.sampled_from([
    None,
    42,
    "hello",
    lambda x: x * 2,
    {"key": "value"},
    [1, 2, 3],
]))
def test_fire_with_empty_command(component):
    """Test that Fire handles various component types with empty command."""
    try:
        # Fire with empty command should work
        result = fire.Fire(component, command=[])
        # Should return the component or its result
        assert result is not None or component is None
    except fire.core.FireExit as e:
        # FireExit with code 0 is OK (help/trace)
        assert e.code in [0, 2]
    except Exception:
        # Some components might not be directly callable
        pass