#!/usr/bin/env python3
"""Additional property-based tests to find more bugs in fire.core"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
import pytest

from fire import core
from fire import parser


@given(st.lists(st.text()), st.integers(min_value=0, max_value=10))
def test_separate_flag_args_multiple_separators(args, num_separators):
    """Test behavior with multiple -- separators."""
    # Insert separators at random positions
    test_args = args.copy()
    for _ in range(min(num_separators, len(test_args) + 1)):
        if test_args:
            pos = len(test_args) // 2
            test_args.insert(pos, '--')
    
    fire_args, flag_args = parser.SeparateFlagArgs(test_args)
    
    # Verify it uses the LAST separator
    if '--' in test_args:
        last_idx = len(test_args) - 1 - test_args[::-1].index('--')
        assert fire_args == test_args[:last_idx]
        assert flag_args == test_args[last_idx + 1:]


@given(st.text())
def test_parse_value_binop_rejection(s):
    """Test that binary operations are rejected."""
    # According to tests, things like '1+1' and '2017-10-10' should be strings
    if '+' in s or '-' in s:
        if s.count('+') == 1 and '+' not in (s[0], s[-1]):
            parts = s.split('+')
            try:
                # If both parts are numbers, it should still be a string
                int(parts[0])
                int(parts[1])
                result = parser.DefaultParseValue(s)
                assert isinstance(result, str)
            except ValueError:
                pass


@given(st.text(alphabet='#', min_size=1))
def test_comment_stripping(s):
    """Test comment handling with #."""
    # Comments should be stripped from unquoted literals
    result = parser.DefaultParseValue(s)
    # Multiple # should still work
    assert result is not None


@given(st.text())
def test_parse_value_syntax_errors(s):
    """Test that syntax errors return the string unchanged."""
    # Single quote, unclosed brackets, etc. should return as string
    if s in ['"', "'", '[', '{', '(']:
        result = parser.DefaultParseValue(s)
        assert result == s


@given(st.one_of(
    st.just('True'),
    st.just('False'),
    st.just('None')
))
def test_bareword_constants(word):
    """Test that Python constants are parsed correctly."""
    result = parser.DefaultParseValue(word)
    if word == 'True':
        assert result is True
    elif word == 'False':
        assert result is False
    elif word == 'None':
        assert result is None


@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz_', min_size=1, max_size=20))
def test_parse_keyword_args_equals_handling(flag_name):
    """Test --flag= (equals with no value) handling."""
    
    class MockSpec:
        def __init__(self):
            self.args = [flag_name]
            self.kwonlyargs = []
            self.varkw = None
    
    # Test with equals but no value
    args = [f'--{flag_name}=']
    fn_spec = MockSpec()
    
    kwargs, remaining_kwargs, remaining_args = core._ParseKeywordArgs(args, fn_spec)
    
    # Should parse the empty string as value
    if flag_name in kwargs:
        assert kwargs[flag_name] == ''


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])