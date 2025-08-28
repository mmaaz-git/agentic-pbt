#!/usr/bin/env python3
"""Property-based tests for fire.docstrings module."""

import re
import sys
import math
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from fire import docstrings


@given(st.text())
def test_parse_never_crashes(docstring):
    """Test that parse() never crashes on any string input.
    
    The docstring for parse() explicitly claims:
    "It does aim to run without crashing in O(n) time on all strings on length n."
    """
    result = docstrings.parse(docstring)
    assert isinstance(result, docstrings.DocstringInfo)


@given(st.lists(st.text()))
def test_strip_blank_lines_length_invariant(lines):
    """Test that _strip_blank_lines never increases the number of lines."""
    original_len = len(lines)
    result = docstrings._strip_blank_lines(lines)
    assert len(result) <= original_len


@given(st.lists(st.text()))
def test_strip_blank_lines_preserves_non_blank(lines):
    """Test that _strip_blank_lines preserves all non-blank lines in the middle."""
    result = docstrings._strip_blank_lines(lines)
    
    # Find first and last non-blank in original
    first_non_blank = None
    last_non_blank = None
    for i, line in enumerate(lines):
        if not docstrings._is_blank(line):
            if first_non_blank is None:
                first_non_blank = i
            last_non_blank = i
    
    if first_non_blank is not None:
        # All non-blank lines between first and last should be preserved
        expected = lines[first_non_blank:last_non_blank + 1]
        assert result == expected


@given(st.text())
def test_is_blank_consistency(line):
    """Test that _is_blank correctly identifies blank lines."""
    result = docstrings._is_blank(line)
    # A line is blank if it's empty or contains only whitespace
    expected = not line or line.isspace()
    assert result == expected


@given(st.text())
def test_is_arg_name_valid_identifier(name):
    """Test that _is_arg_name only accepts valid Python identifiers."""
    result = docstrings._is_arg_name(name)
    
    # According to the implementation, valid arg names match r'^[a-zA-Z_]\w*$'
    name_stripped = name.strip()
    pattern = r'^[a-zA-Z_]\w*$'
    expected = bool(re.match(pattern, name_stripped))
    
    assert result == expected


@given(st.text())
def test_line_is_hyphens_correctness(line):
    """Test that _line_is_hyphens correctly identifies hyphen-only lines."""
    result = docstrings._line_is_hyphens(line)
    
    # According to implementation: line and not line.strip('-')
    # This means: line is not empty AND stripping all hyphens leaves empty string
    expected = bool(line and not line.strip('-'))
    
    assert result == expected


@given(st.lists(st.text(min_size=1)))
def test_join_lines_preserves_non_empty_content(lines):
    """Test that _join_lines preserves all non-empty content."""
    result = docstrings._join_lines(lines)
    
    # Count non-empty lines in input
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    
    if non_empty_lines:
        # Result should contain all non-empty content
        assert result is not None
        for line in non_empty_lines:
            # Each non-empty line should appear in the result
            assert line in result
    else:
        # If all lines are empty, result should be None
        assert result is None


@given(st.text())
def test_cast_to_known_type_removes_trailing_dot(type_str):
    """Test that _cast_to_known_type removes trailing dots."""
    result = docstrings._cast_to_known_type(type_str)
    
    if type_str is None:
        assert result is None
    else:
        expected = type_str.rstrip('.')
        assert result == expected


@given(st.text())
def test_as_arg_name_and_type_parsing(text):
    """Test that _as_arg_name_and_type correctly parses 'name (type)' format."""
    result = docstrings._as_arg_name_and_type(text)
    
    tokens = text.split()
    if len(tokens) >= 2:
        first_token = tokens[0]
        if docstrings._is_arg_name(first_token):
            # Should return (name, type)
            assert result is not None
            assert result[0] == first_token
            # Type should be rest of tokens with parentheses stripped
            type_part = ' '.join(tokens[1:])
            type_clean = type_part.lstrip('{([').rstrip('])}')
            assert result[1] == type_clean
        else:
            assert result is None
    else:
        assert result is None


@given(st.text())
def test_as_arg_names_comma_space_separation(names_str):
    """Test that _as_arg_names correctly parses comma/space separated names."""
    result = docstrings._as_arg_names(names_str)
    
    # Split by comma or space
    names = re.split(',| ', names_str)
    names = [name.strip() for name in names if name.strip()]
    
    # Check if all are valid arg names
    all_valid = all(docstrings._is_arg_name(name) for name in names)
    
    if names and all_valid:
        assert result == names
    else:
        assert result is None


@given(st.text())
def test_get_directive_extraction(line_content):
    """Test _get_directive extracts RST directive correctly."""
    # Create a line_info-like object
    class LineInfo:
        def __init__(self, content):
            self.stripped = content.strip()
    
    line_info = LineInfo(line_content)
    result = docstrings._get_directive(line_info)
    
    stripped = line_content.strip()
    if stripped.startswith(':'):
        parts = stripped.split(':', 2)
        if len(parts) >= 2:
            expected = parts[1]
            assert result == expected
        else:
            assert result == ''
    else:
        assert result is None


@given(st.sampled_from(['Args', 'Returns', 'Yields', 'Raises', 'args', 'ARGS', 'returns', 'Yield']))
def test_section_matching_case_insensitive(title):
    """Test that section matching is case-insensitive and handles plurals."""
    # This tests the _section_from_possible_title function
    result = docstrings._section_from_possible_title(title)
    
    # Should match known sections case-insensitively
    title_lower = title.lower()
    if title_lower in ('args', 'arg'):
        assert result == docstrings.Sections.ARGS
    elif title_lower in ('returns', 'return'):
        assert result == docstrings.Sections.RETURNS
    elif title_lower in ('yields', 'yield'):
        assert result == docstrings.Sections.YIELDS
    elif title_lower in ('raises', 'raise'):
        assert result == docstrings.Sections.RAISES
    else:
        # Unknown sections
        assert result in (docstrings.Sections.ARGS, docstrings.Sections.RETURNS, 
                         docstrings.Sections.YIELDS, docstrings.Sections.RAISES, None)


@given(st.text(min_size=1, max_size=10000))
@settings(max_examples=1000)
def test_parse_performance(docstring):
    """Test that parse() runs in reasonable time for strings up to 10KB."""
    import time
    start = time.time()
    result = docstrings.parse(docstring)
    elapsed = time.time() - start
    
    # Should complete in less than 1 second for 10KB string
    assert elapsed < 1.0
    assert isinstance(result, docstrings.DocstringInfo)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])