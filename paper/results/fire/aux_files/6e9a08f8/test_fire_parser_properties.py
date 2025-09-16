#!/usr/bin/env python3
"""Property-based tests for fire.parser module using Hypothesis."""

import sys
import os
import ast
import datetime

# Add the fire package to path
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import parser
from hypothesis import given, strategies as st, assume, settings, example
import pytest
import math

# Strategy for command-line arguments (non-empty strings without certain special chars)
cmd_arg = st.text(min_size=1).filter(lambda x: '\0' not in x and x.strip())

# Strategy for safe strings that won't break parsing
safe_string = st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cf')), min_size=0, max_size=100)

# Strategy for numbers
safe_float = st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)
safe_int = st.integers(min_value=-10**10, max_value=10**10)


class TestSeparateFlagArgs:
    """Test properties of the SeparateFlagArgs function."""
    
    @given(st.lists(cmd_arg))
    def test_element_preservation_no_separator(self, args):
        """Without '--', all args should be in fire_args."""
        # Remove any '--' from the list to test this property
        args = [arg for arg in args if arg != '--']
        fire_args, flag_args = parser.SeparateFlagArgs(args)
        
        assert fire_args == args
        assert flag_args == []
        assert len(fire_args) + len(flag_args) == len(args)
    
    @given(st.lists(cmd_arg), st.integers(min_value=0, max_value=5))
    def test_single_separator_splits_correctly(self, args, separator_pos):
        """A single '--' should split args correctly."""
        # Remove existing '--' and insert exactly one
        args = [arg for arg in args if arg != '--']
        if len(args) == 0:
            return  # Skip empty lists
        
        # Insert '--' at a valid position
        separator_pos = min(separator_pos, len(args))
        test_args = args[:separator_pos] + ['--'] + args[separator_pos:]
        
        fire_args, flag_args = parser.SeparateFlagArgs(test_args)
        
        # Verify the split
        assert fire_args == args[:separator_pos]
        assert flag_args == args[separator_pos:]
        assert len(fire_args) + len(flag_args) + 1 == len(test_args)  # +1 for '--'
    
    @given(st.lists(cmd_arg))
    def test_last_separator_matters(self, args):
        """Only the last '--' should matter for splitting."""
        # Remove existing '--' 
        args = [arg for arg in args if arg != '--']
        if len(args) < 3:
            return
        
        # Add multiple '--' separators
        test_args = [args[0], '--'] + args[1:2] + ['--'] + args[2:]
        
        fire_args, flag_args = parser.SeparateFlagArgs(test_args)
        
        # The last '--' is what matters
        expected_fire = [args[0], '--'] + args[1:2]
        expected_flag = args[2:]
        
        assert fire_args == expected_fire
        assert flag_args == expected_flag


class TestDefaultParseValue:
    """Test properties of the DefaultParseValue function."""
    
    @given(safe_int)
    def test_integer_parsing(self, n):
        """Integers should be parsed correctly."""
        result = parser.DefaultParseValue(str(n))
        assert result == n
        assert isinstance(result, int)
    
    @given(safe_float.filter(lambda x: not x.is_integer()))
    def test_float_parsing(self, x):
        """Floats should be parsed correctly."""
        result = parser.DefaultParseValue(str(x))
        # Use isclose for float comparison
        assert math.isclose(result, x, rel_tol=1e-9, abs_tol=1e-10)
        assert isinstance(result, float)
    
    @given(st.sampled_from([True, False, None]))
    def test_special_constants(self, value):
        """Python constants should be parsed correctly."""
        str_value = str(value)  # 'True', 'False', or 'None'
        result = parser.DefaultParseValue(str_value)
        assert result == value
    
    @given(safe_string)
    def test_quoted_string_preservation(self, s):
        """Quoted strings should preserve their content."""
        # Test single quotes
        single_quoted = f"'{s}'"
        if "'" not in s:  # Only test if string doesn't contain single quotes
            try:
                result = parser.DefaultParseValue(single_quoted)
                assert result == s
            except:
                pass  # Some strings might still fail parsing
        
        # Test double quotes
        double_quoted = f'"{s}"'
        if '"' not in s:  # Only test if string doesn't contain double quotes
            try:
                result = parser.DefaultParseValue(double_quoted)
                assert result == s
            except:
                pass
    
    @given(st.lists(safe_int, max_size=10))
    def test_list_parsing(self, lst):
        """Lists should be parsed correctly."""
        list_str = str(lst)
        result = parser.DefaultParseValue(list_str)
        assert result == lst
        assert isinstance(result, list)
    
    @given(st.dictionaries(
        st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=5),
        safe_int,
        max_size=5
    ))
    def test_dict_parsing(self, d):
        """Dictionaries should be parsed correctly."""
        dict_str = str(d)
        result = parser.DefaultParseValue(dict_str)
        assert result == d
        assert isinstance(result, dict)
    
    @given(st.tuples(safe_int, safe_int, safe_int))
    def test_tuple_parsing(self, t):
        """Tuples should be parsed correctly."""
        tuple_str = str(t)
        result = parser.DefaultParseValue(tuple_str)
        assert result == t
        assert isinstance(result, tuple)
    
    def test_binary_operations_as_strings(self):
        """Binary operations should be treated as strings."""
        assert parser.DefaultParseValue('1+1') == '1+1'
        assert parser.DefaultParseValue('2-1') == '2-1'
        assert parser.DefaultParseValue('3*4') == '3*4'
        assert parser.DefaultParseValue('10/2') == '10/2'
        assert parser.DefaultParseValue('2017-10-10') == '2017-10-10'
    
    def test_special_number_formats(self):
        """Scientific notation should be parsed correctly."""
        assert parser.DefaultParseValue('1e5') == 100000.0
        assert parser.DefaultParseValue('1e-3') == 0.001
        assert parser.DefaultParseValue('2.5e2') == 250.0
    
    @given(st.text(min_size=1, max_size=20))
    def test_unparseable_strings_remain_strings(self, s):
        """Strings that can't be parsed should remain as strings."""
        # Add some characters that will make it unparseable as Python literal
        test_str = f"[{s}..."  # Unclosed bracket
        result = parser.DefaultParseValue(test_str)
        assert result == test_str
        assert isinstance(result, str)
    
    def test_nested_quotes(self):
        """Nested quotes should be handled correctly."""
        assert parser.DefaultParseValue('"\'123\'"') == "'123'"
        assert parser.DefaultParseValue("'\"456\"'") == '"456"'
    
    def test_yaml_like_dict_syntax(self):
        """YAML-like dict syntax with bare words should work."""
        result = parser.DefaultParseValue('{a: 1, b: 2}')
        assert result == {'a': 1, 'b': 2}
        
        result = parser.DefaultParseValue('{name: John, age: 30}')
        assert result == {'name': 'John', 'age': 30}
    
    def test_bare_words_in_containers(self):
        """Bare words in containers should be converted to strings."""
        assert parser.DefaultParseValue('[one, two, three]') == ['one', 'two', 'three']
        assert parser.DefaultParseValue('(alpha, beta, gamma)') == ('alpha', 'beta', 'gamma')
        assert parser.DefaultParseValue('[hello, 123, world]') == ['hello', 123, 'world']
    
    def test_comments_are_stripped(self):
        """Comments after # should be stripped in non-string contexts."""
        assert parser.DefaultParseValue('123#comment') == 123
        assert parser.DefaultParseValue('[1, 2]#comment') == [1, 2]
        # But preserved in quoted strings
        assert parser.DefaultParseValue('"#notacomment"') == '#notacomment'
    
    @given(st.lists(st.lists(safe_int, max_size=3), max_size=3))
    def test_nested_lists(self, nested_list):
        """Nested lists should be parsed correctly."""
        list_str = str(nested_list)
        result = parser.DefaultParseValue(list_str)
        assert result == nested_list
    
    def test_mixed_containers(self):
        """Mixed nested containers should parse correctly."""
        test_str = '[(1, 2), {"a": 3}, [4, 5]]'
        expected = [(1, 2), {"a": 3}, [4, 5]]
        assert parser.DefaultParseValue(test_str) == expected
    
    def test_empty_containers(self):
        """Empty containers should parse correctly."""
        assert parser.DefaultParseValue('[]') == []
        assert parser.DefaultParseValue('{}') == {}
        assert parser.DefaultParseValue('()') == ()
    
    def test_special_dash_strings(self):
        """Dash strings should be preserved."""
        assert parser.DefaultParseValue('-') == '-'
        assert parser.DefaultParseValue('--') == '--'
        assert parser.DefaultParseValue('---') == '---'
        assert parser.DefaultParseValue('----') == '----'


class TestLiteralEval:
    """Test properties of the _LiteralEval function."""
    
    def test_binop_rejection(self):
        """Binary operations should be rejected."""
        with pytest.raises(ValueError):
            parser._LiteralEval('1+1')
        with pytest.raises(ValueError):
            parser._LiteralEval('2*3')
        with pytest.raises(ValueError):
            parser._LiteralEval('10-5')
    
    def test_bare_word_conversion(self):
        """Bare words should be converted to strings."""
        assert parser._LiteralEval('hello') == 'hello'
        assert parser._LiteralEval('[hello, world]') == ['hello', 'world']
        assert parser._LiteralEval('{key: value}') == {'key': 'value'}
    
    def test_preserved_constants(self):
        """True, False, None should not be converted to strings."""
        assert parser._LiteralEval('True') is True
        assert parser._LiteralEval('False') is False
        assert parser._LiteralEval('None') is None
        assert parser._LiteralEval('[True, False, None]') == [True, False, None]
    
    @given(st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cf')), min_size=1, max_size=20))
    def test_syntax_errors_propagate(self, bad_syntax):
        """Syntax errors should propagate."""
        # Create definitely invalid syntax
        test_str = f"{{{{[{bad_syntax}"  # Multiple unclosed brackets
        with pytest.raises(SyntaxError):
            parser._LiteralEval(test_str)


class TestRoundTripProperties:
    """Test round-trip properties where applicable."""
    
    @given(st.one_of(
        safe_int,
        safe_float,
        st.booleans(),
        st.none(),
        st.lists(safe_int, max_size=5),
        st.dictionaries(st.text(alphabet='abcdef', min_size=1, max_size=3), safe_int, max_size=3)
    ))
    def test_value_string_roundtrip(self, value):
        """Converting a value to string and parsing should return the same value."""
        string_repr = str(value)
        parsed = parser.DefaultParseValue(string_repr)
        
        if isinstance(value, float):
            assert math.isclose(parsed, value, rel_tol=1e-9, abs_tol=1e-10)
        else:
            assert parsed == value


if __name__ == '__main__':
    # Run with increased examples for better coverage
    pytest.main([__file__, '-v', '--tb=short'])