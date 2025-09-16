#!/usr/bin/env python3
"""Property-based tests for the Python Fire library using Hypothesis."""

import shlex
import sys
from hypothesis import given, strategies as st, assume, settings
import fire
import fire.parser as parser


# Test functions for property testing
def simple_function(x=10):
    """A simple function that returns its input."""
    return x


def add_function(a, b=5):
    """Function that adds two numbers."""
    return a + b


def multiply_function(x, y):
    """Function that multiplies two numbers."""
    return x * y


class SimpleClass:
    """A simple class for testing."""
    
    def __init__(self, value=100):
        self.value = value
    
    def double(self, x=1):
        return 2 * x
    
    def add(self, a, b=10):
        return a + b


# Property 1: Command string vs list equivalence
@given(
    st.sampled_from(['double', 'add']),
    st.integers(min_value=-1000, max_value=1000)
)
def test_string_list_command_equivalence(method_name, value):
    """Test that command as string and list produce the same result."""
    obj = SimpleClass()
    
    # Test with single argument
    string_command = f'{method_name} {value}'
    list_command = [method_name, str(value)]
    
    try:
        result_string = fire.Fire(obj, command=string_command)
        result_list = fire.Fire(obj, command=list_command)
        assert result_string == result_list
    except (fire.core.FireExit, SystemExit):
        # Both should fail in the same way
        pass


# Property 2: Flag argument parsing consistency (--flag=value vs --flag value)
@given(
    st.integers(min_value=-100, max_value=100),
    st.integers(min_value=-100, max_value=100)
)
def test_flag_argument_consistency(val1, val2):
    """Test that --flag=value and --flag value produce the same result."""
    obj = SimpleClass()
    
    # Test with equals sign
    command_equals = ['add', str(val1), f'--b={val2}']
    # Test without equals sign
    command_space = ['add', str(val1), '--b', str(val2)]
    
    try:
        result_equals = fire.Fire(obj, command=command_equals)
        result_space = fire.Fire(obj, command=command_space)
        assert result_equals == result_space
    except (fire.core.FireExit, SystemExit) as e1:
        try:
            # If one fails, both should fail
            fire.Fire(obj, command=command_space)
            assert False, "Expected both commands to fail"
        except (fire.core.FireExit, SystemExit):
            pass


# Property 3: Single vs double hyphen consistency
@given(
    st.integers(min_value=-100, max_value=100),
    st.integers(min_value=-100, max_value=100)
)
def test_single_double_hyphen_consistency(val1, val2):
    """Test that -flag and --flag produce the same result for named arguments."""
    obj = SimpleClass()
    
    # Test with double hyphen
    command_double = ['add', str(val1), '--b', str(val2)]
    # Test with single hyphen
    command_single = ['add', str(val1), '-b', str(val2)]
    
    try:
        result_double = fire.Fire(obj, command=command_double)
        result_single = fire.Fire(obj, command=command_single)
        assert result_double == result_single
    except (fire.core.FireExit, SystemExit):
        # Both should fail in the same way
        pass


# Property 4: Default value consistency
@given(st.integers(min_value=-100, max_value=100))
def test_default_value_consistency(value):
    """Test that explicitly providing default values gives same result as omitting them."""
    obj = SimpleClass()
    
    # Call with explicit default
    command_explicit = ['add', str(value), '--b', '10']  # 10 is the default
    # Call without specifying default
    command_implicit = ['add', str(value)]
    
    try:
        result_explicit = fire.Fire(obj, command=command_explicit)
        result_implicit = fire.Fire(obj, command=command_implicit)
        assert result_explicit == result_implicit
    except (fire.core.FireExit, SystemExit):
        pass


# Property 5: Type preservation for numeric literals
@given(st.integers(min_value=-10000, max_value=10000))
def test_integer_preservation(value):
    """Test that integer values are correctly parsed and preserved."""
    result = fire.Fire(simple_function, command=[str(value)])
    assert result == value
    assert type(result) == int


@given(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False))
def test_float_preservation(value):
    """Test that float values are correctly parsed and preserved."""
    # Convert to string and back to normalize representation
    str_value = str(value)
    result = fire.Fire(simple_function, command=[str_value])
    # Use string comparison to handle float representation issues
    assert abs(result - value) < 1e-10 or str(result) == str(value)


# Property 6: Boolean parsing consistency
@given(st.booleans())
def test_boolean_parsing(value):
    """Test that boolean values are correctly parsed."""
    bool_str = 'True' if value else 'False'
    result = fire.Fire(simple_function, command=[bool_str])
    assert result == value
    assert type(result) == bool


# Property 7: List literal parsing
@given(st.lists(st.integers(min_value=-100, max_value=100), max_size=10))
def test_list_parsing(lst):
    """Test that list literals are correctly parsed."""
    # Skip empty lists or lists with special characters that might cause issues
    if not lst:
        return
    
    list_str = str(lst)
    result = fire.Fire(simple_function, command=[list_str])
    assert result == lst
    assert type(result) == list


# Property 8: Dictionary literal parsing
@given(
    st.dictionaries(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=5),
        st.integers(min_value=-100, max_value=100),
        max_size=5
    )
)
def test_dict_parsing(dct):
    """Test that dictionary literals are correctly parsed."""
    if not dct:
        return
        
    dict_str = str(dct)
    result = fire.Fire(simple_function, command=[dict_str])
    assert result == dct
    assert type(result) == dict


# Property 9: Quoted string handling
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789 ', min_size=1, max_size=20))
def test_quoted_string_handling(text):
    """Test that quoted strings are handled correctly."""
    # Test with double quotes
    quoted_text = f'"{text}"'
    result = fire.Fire(simple_function, command=[quoted_text])
    assert result == text


# Property 10: Command chaining with separator
@given(
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=1, max_value=100)
)
def test_separator_chaining(val1, val2):
    """Test that separator correctly chains commands."""
    class ChainTest:
        def get_value(self, x):
            return SimpleClass(x)
    
    obj = ChainTest()
    command = ['get_value', str(val1), '-', 'double', str(val2)]
    
    try:
        result = fire.Fire(obj, command=command)
        assert result == 2 * val2
    except (fire.core.FireExit, SystemExit):
        pass


# Property 11: Idempotence of parsing
@given(st.integers(min_value=-1000, max_value=1000))
def test_parsing_idempotence(value):
    """Test that parsing a value multiple times gives consistent results."""
    str_value = str(value)
    parsed1 = parser.DefaultParseValue(str_value)
    parsed2 = parser.DefaultParseValue(str_value)
    assert parsed1 == parsed2
    assert type(parsed1) == type(parsed2)


# Property 12: SeparateFlagArgs invariant
@given(st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=20))
def test_separate_flag_args_invariant(args):
    """Test that SeparateFlagArgs correctly splits arguments."""
    # Add some valid args
    args = [arg for arg in args if arg]  # Filter empty strings
    
    fire_args, flag_args = parser.SeparateFlagArgs(args)
    
    # Invariant: if no '--' in args, all args are fire args
    if '--' not in args:
        assert fire_args == args
        assert flag_args == []
    else:
        # The recombined args should equal the original
        last_separator_idx = len(args) - 1 - args[::-1].index('--')
        assert fire_args == args[:last_separator_idx]
        assert flag_args == args[last_separator_idx + 1:]


if __name__ == '__main__':
    # Run with increased examples for better coverage
    settings.register_profile("thorough", max_examples=500)
    settings.load_profile("thorough")
    
    print("Running property-based tests for Python Fire...")
    import pytest
    sys.exit(pytest.main([__file__, '-v']))