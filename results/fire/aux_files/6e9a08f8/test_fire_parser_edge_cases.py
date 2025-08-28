#!/usr/bin/env python3
"""Additional edge case tests for fire.parser module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import parser
from hypothesis import given, strategies as st, assume, settings, example
import pytest

# Test for potential edge cases and bugs

class TestParserEdgeCases:
    """Test edge cases that might reveal bugs."""
    
    def test_comment_handling_edge_cases(self):
        """Test edge cases with comment handling."""
        # Comments should be stripped in numeric contexts
        assert parser.DefaultParseValue('42#comment') == 42
        assert parser.DefaultParseValue('3.14#pi') == 3.14
        
        # But what about strings that look like they have comments?
        assert parser.DefaultParseValue('"text#notacomment"') == 'text#notacomment'
        
        # Complex cases
        assert parser.DefaultParseValue('[1, 2]#list comment') == [1, 2]
        assert parser.DefaultParseValue('{"a": 1}#dict comment') == {'a': 1}
        
        # Edge case: What about nested structures with comments?
        assert parser.DefaultParseValue('[[1, 2], 3]#nested') == [[1, 2], 3]
    
    def test_quote_escaping_edge_cases(self):
        """Test edge cases with quote escaping."""
        # Test strings with escaped quotes
        test_cases = [
            ('"\\"hello\\""', '"hello"'),  # Escaped double quotes
            ("'\\'hello\\''", "'hello'"),  # Escaped single quotes
        ]
        
        for input_str, expected in test_cases:
            try:
                result = parser.DefaultParseValue(input_str)
                # The parser may not handle these correctly
                print(f"Input: {input_str}, Expected: {expected}, Got: {result}")
            except Exception as e:
                print(f"Failed to parse {input_str}: {e}")
    
    def test_whitespace_handling(self):
        """Test how whitespace is handled."""
        # Leading/trailing whitespace in bare strings
        assert parser.DefaultParseValue('  42  ') == 42
        assert parser.DefaultParseValue('  True  ') == True
        
        # Whitespace in containers
        assert parser.DefaultParseValue('[  1,  2,  3  ]') == [1, 2, 3]
        assert parser.DefaultParseValue('{ "a" : 1 , "b" : 2 }') == {'a': 1, 'b': 2}
    
    def test_special_numeric_values(self):
        """Test special numeric values."""
        # Very large numbers
        assert parser.DefaultParseValue('999999999999999999999') == 999999999999999999999
        
        # Very small floats
        assert parser.DefaultParseValue('0.000000000000001') == 0.000000000000001
        
        # Negative zero
        result = parser.DefaultParseValue('-0.0')
        assert result == 0.0 or result == -0.0  # Both are acceptable
        
        # Hexadecimal, octal, binary - these likely won't work
        # but let's see what happens
        for test_val in ['0x10', '0o10', '0b10']:
            result = parser.DefaultParseValue(test_val)
            print(f"Parsing {test_val}: {result} (type: {type(result)})")
    
    def test_unicode_handling(self):
        """Test Unicode characters in strings."""
        # Emoji and special characters
        assert parser.DefaultParseValue('"🔥"') == '🔥'
        assert parser.DefaultParseValue('"Hello 世界"') == 'Hello 世界'
        assert parser.DefaultParseValue('["🎈", "🎉"]') == ['🎈', '🎉']
    
    def test_empty_and_whitespace_strings(self):
        """Test empty and whitespace-only strings."""
        assert parser.DefaultParseValue('""') == ''
        assert parser.DefaultParseValue("''") == ''
        assert parser.DefaultParseValue('" "') == ' '
        assert parser.DefaultParseValue('"  "') == '  '
    
    def test_nested_container_edge_cases(self):
        """Test deeply nested containers."""
        # Very deep nesting
        deep_list = '[[[[1]]]]'
        assert parser.DefaultParseValue(deep_list) == [[[[1]]]]
        
        # Mixed deep nesting
        mixed = '[{"a": [(1, 2)]}]'
        assert parser.DefaultParseValue(mixed) == [{"a": [(1, 2)]}]
    
    def test_yaml_dict_with_special_keys(self):
        """Test YAML-like dict syntax with special keys."""
        # Keys that are Python keywords
        assert parser.DefaultParseValue('{True: 1, False: 0}') == {True: 1, False: 0}
        assert parser.DefaultParseValue('{None: "null"}') == {None: "null"}
        
        # Numeric keys
        assert parser.DefaultParseValue('{1: "one", 2: "two"}') == {1: "one", 2: "two"}
    
    def test_string_that_looks_like_code(self):
        """Test strings that look like Python code."""
        # These should remain as strings since they contain operators
        assert parser.DefaultParseValue('x = 10') == 'x = 10'
        assert parser.DefaultParseValue('if True: pass') == 'if True: pass'
        assert parser.DefaultParseValue('lambda x: x') == 'lambda x: x'
    
    def test_malformed_containers(self):
        """Test malformed container literals."""
        # These should be treated as strings
        assert parser.DefaultParseValue('[1, 2,') == '[1, 2,'
        assert parser.DefaultParseValue('{a: 1') == '{a: 1'
        assert parser.DefaultParseValue('(1, 2,') == '(1, 2,'
    
    def test_separator_flag_args_edge_cases(self):
        """Test edge cases for SeparateFlagArgs."""
        # Empty list
        assert parser.SeparateFlagArgs([]) == ([], [])
        
        # Only separator
        assert parser.SeparateFlagArgs(['--']) == ([], [])
        
        # Multiple consecutive separators
        assert parser.SeparateFlagArgs(['--', '--']) == (['--'], [])
        assert parser.SeparateFlagArgs(['a', '--', '--', 'b']) == (['a', '--'], ['b'])
        
        # Separator-like strings that aren't exactly '--'
        assert parser.SeparateFlagArgs(['---']) == (['---'], [])
        assert parser.SeparateFlagArgs(['- -']) == (['- -'], [])
    
    def test_quoted_special_values(self):
        """Test quoting of special Python values."""
        # Quoted versions should be strings
        assert parser.DefaultParseValue('"None"') == 'None'
        assert parser.DefaultParseValue('"True"') == 'True' 
        assert parser.DefaultParseValue('"False"') == 'False'
        assert parser.DefaultParseValue("'None'") == 'None'
        assert parser.DefaultParseValue("'True'") == 'True'
        assert parser.DefaultParseValue("'False'") == 'False'
    
    def test_mixed_quote_types(self):
        """Test mixing quote types."""
        # List with mixed quote types
        result = parser.DefaultParseValue('["double", \'single\']')
        assert result == ["double", "single"]
        
        # Dict with mixed quotes
        result = parser.DefaultParseValue('{"key1": \'value1\', "key2": "value2"}')
        assert result == {"key1": "value1", "key2": "value2"}
    
    def test_tuple_vs_expression(self):
        """Test disambiguation between tuples and expressions."""
        # Single element tuple needs trailing comma
        assert parser.DefaultParseValue('(1,)') == (1,)
        
        # Without comma, parentheses are just grouping
        assert parser.DefaultParseValue('(1)') == 1
        
        # Multiple elements don't need trailing comma
        assert parser.DefaultParseValue('(1, 2)') == (1, 2)
    
    def test_raw_literal_eval_edge_cases(self):
        """Test _LiteralEval directly for edge cases."""
        # Test that bare words are converted
        assert parser._LiteralEval('hello') == 'hello'
        
        # Test that True/False/None are preserved
        assert parser._LiteralEval('[True, hello, None]') == [True, 'hello', None]
        
        # Test binary operations are rejected
        with pytest.raises(ValueError):
            parser._LiteralEval('2 + 2')
        
        with pytest.raises(ValueError):
            parser._LiteralEval('10 - 5')
    
    @given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=10))
    def test_arbitrary_ascii_strings(self, s):
        """Test that arbitrary ASCII strings don't crash the parser."""
        try:
            result = parser.DefaultParseValue(s)
            # Should either parse to something or remain as string
            assert result is not None
        except Exception as e:
            # Parser should not crash on any ASCII input
            pytest.fail(f"Parser crashed on input '{s}': {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])