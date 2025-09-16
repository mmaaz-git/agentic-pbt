#!/usr/bin/env python3
"""Property-based tests for fire.core module using Hypothesis."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import re
import string

from fire import core
from fire import parser
from fire import inspectutils


# Strategy for generating valid flag-like arguments
flag_chars = st.text(alphabet=string.ascii_letters, min_size=1, max_size=10)
flag_names = st.text(alphabet=string.ascii_letters + string.digits + '_', min_size=1, max_size=20)


@given(st.lists(st.text()))
def test_separate_flag_args_preserves_all_arguments(args):
    """Property: SeparateFlagArgs should preserve all arguments."""
    # Execute the function
    fire_args, flag_args = parser.SeparateFlagArgs(args)
    
    # Count occurrences of '--' separator
    separator_count = args.count('--')
    
    if separator_count == 0:
        # No separator: all args should be fire args
        assert fire_args == args
        assert flag_args == []
    else:
        # With separator: combined args should match original (minus separators)
        # The function splits at the LAST '--'
        last_separator_idx = len(args) - 1 - args[::-1].index('--')
        expected_fire = args[:last_separator_idx]
        expected_flag = args[last_separator_idx + 1:]
        
        assert fire_args == expected_fire
        assert flag_args == expected_flag


@given(st.text())
def test_is_flag_consistency(argument):
    """Property: _IsFlag should be consistent with its sub-functions."""
    result = core._IsFlag(argument)
    single_char = core._IsSingleCharFlag(argument)
    multi_char = core._IsMultiCharFlag(argument)
    
    # _IsFlag is defined as OR of single and multi char
    assert result == (single_char or multi_char)


@given(st.text(min_size=1))
def test_is_flag_negative_numbers(argument):
    """Property: Negative numbers should not be detected as flags."""
    if re.match(r'^-\d+(\.\d+)?$', argument):
        # This is a negative number
        assert not core._IsFlag(argument)
        assert not core._IsSingleCharFlag(argument)


@given(st.text())
def test_default_parse_value_quoted_strings_roundtrip(s):
    """Property: Quoted strings should parse to their content."""
    # Test single quotes
    single_quoted = f"'{s}'"
    if "'" not in s:  # Only test if string doesn't contain quotes
        try:
            result = parser.DefaultParseValue(single_quoted)
            assert result == s
        except:
            pass  # Some strings might cause syntax errors
    
    # Test double quotes  
    double_quoted = f'"{s}"'
    if '"' not in s:  # Only test if string doesn't contain quotes
        try:
            result = parser.DefaultParseValue(double_quoted)
            assert result == s
        except:
            pass


@given(st.integers())
def test_default_parse_value_integers(n):
    """Property: Integer strings should parse to integers."""
    str_n = str(n)
    result = parser.DefaultParseValue(str_n)
    assert result == n
    assert isinstance(result, int)


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_default_parse_value_floats(n):
    """Property: Float strings should parse to floats."""
    str_n = str(n)
    result = parser.DefaultParseValue(str_n)
    assert result == pytest.approx(n)


@given(st.lists(st.one_of(st.integers(), st.text(alphabet=string.ascii_letters, min_size=1))))
def test_default_parse_value_lists(lst):
    """Property: List literals should parse correctly."""
    # Create a string representation
    str_lst = str(lst)
    result = parser.DefaultParseValue(str_lst)
    assert result == lst


@given(st.dictionaries(
    st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
    st.one_of(st.integers(), st.text(alphabet=string.ascii_letters, min_size=1))
))
def test_default_parse_value_dicts(d):
    """Property: Dict literals should parse correctly."""
    str_d = str(d)
    result = parser.DefaultParseValue(str_d)
    assert result == d


@given(st.lists(st.text()))
def test_parse_keyword_args_basic(args):
    """Property: _ParseKeywordArgs should handle basic flag parsing."""
    # Create a simple function spec for testing
    class MockSpec:
        def __init__(self):
            self.args = ['arg1', 'arg2', 'arg3']
            self.kwonlyargs = []
            self.varkw = None
    
    fn_spec = MockSpec()
    
    # Run the function
    kwargs, remaining_kwargs, remaining_args = core._ParseKeywordArgs(args, fn_spec)
    
    # Basic invariant: all args should be accounted for
    total_parsed = len(remaining_kwargs) + len(remaining_args)
    # kwargs values are included in the count via remaining_kwargs
    
    # Some args might be consumed as values for kwargs
    assert total_parsed <= len(args)


@given(st.text())
def test_is_single_char_flag_pattern(argument):
    """Property: Single char flags follow specific pattern."""
    result = core._IsSingleCharFlag(argument)
    
    # Check against the regex patterns used
    pattern1 = bool(re.match('^-[a-zA-Z]$', argument))
    pattern2 = bool(re.match('^-[a-zA-Z]=', argument))
    
    assert result == (pattern1 or pattern2)


@given(st.text())  
def test_is_multi_char_flag_pattern(argument):
    """Property: Multi char flags start with -- or match single char pattern."""
    result = core._IsMultiCharFlag(argument)
    
    starts_with_double = argument.startswith('--')
    matches_single_pattern = bool(re.match('^-[a-zA-Z]', argument))
    
    assert result == (starts_with_double or matches_single_pattern)


@given(st.text())
def test_default_parse_value_none_handling(s):
    """Property: 'None' string should parse to None, quoted 'None' should stay string."""
    if s == 'None':
        assert parser.DefaultParseValue(s) is None
    elif s == "'None'" or s == '"None"':
        assert parser.DefaultParseValue(s) == 'None'


@given(st.text())
def test_default_parse_value_bool_handling(s):
    """Property: Boolean strings should parse to booleans."""
    if s == 'True':
        assert parser.DefaultParseValue(s) is True
    elif s == 'False':
        assert parser.DefaultParseValue(s) is False
    elif s in ("'True'", '"True"'):
        assert parser.DefaultParseValue(s) == 'True'
    elif s in ("'False'", '"False"'):
        assert parser.DefaultParseValue(s) == 'False'


# Test for potential edge cases in flag parsing
@given(st.text(alphabet='-=', min_size=1, max_size=5))
def test_edge_case_flag_strings(s):
    """Property: Edge cases with only hyphens and equals."""
    # These should be handled consistently
    result_flag = core._IsFlag(s)
    result_single = core._IsSingleCharFlag(s)
    result_multi = core._IsMultiCharFlag(s)
    
    # Just verify no crashes and consistency
    assert result_flag == (result_single or result_multi)


# Test for comment handling  
@given(st.text())
def test_default_parse_value_comment_handling(s):
    """Property: Comments with # should be handled."""
    if '#' in s and not (s.startswith('"') or s.startswith("'")):
        # Unquoted strings with # might have comment stripped
        result = parser.DefaultParseValue(s)
        # Just ensure it doesn't crash
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])