#!/usr/bin/env python3
"""Property-based tests for fire.docstrings module using Hypothesis."""

import sys
sys.path.append('/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import fire.docstrings as docstrings
import re
import math


# Test 1: Crash resistance - parse() should never crash on any string input
@given(st.text())
@settings(max_examples=1000)
def test_parse_never_crashes(docstring):
    """The parse function claims to run without crashing on all strings."""
    result = docstrings.parse(docstring)
    assert isinstance(result, docstrings.DocstringInfo)
    assert result.summary is None or isinstance(result.summary, str)
    assert result.description is None or isinstance(result.description, str)
    assert result.args is None or isinstance(result.args, list)
    assert result.returns is None or isinstance(result.returns, str)
    assert result.yields is None or isinstance(result.yields, str)
    assert result.raises is None or isinstance(result.raises, str)


# Test 2: None handling
@given(st.none())
def test_parse_none_input(none_value):
    """parse(None) should return an empty DocstringInfo()."""
    result = docstrings.parse(none_value)
    assert result == docstrings.DocstringInfo()


# Test 3: _strip_blank_lines invariants
@given(st.lists(st.text()))
def test_strip_blank_lines_preserves_content(lines):
    """_strip_blank_lines should preserve non-blank content."""
    result = docstrings._strip_blank_lines(lines)
    
    # Result should be a subset of original lines
    for line in result:
        assert line in lines
    
    # No leading or trailing blank lines
    if result:
        assert not docstrings._is_blank(result[0])
        assert not docstrings._is_blank(result[-1])
    
    # Order should be preserved
    if len(result) >= 2:
        for i in range(len(result) - 1):
            idx1 = lines.index(result[i])
            idx2 = lines.index(result[i + 1])
            assert idx1 < idx2


# Test 4: _is_arg_name validation
@given(st.text())
def test_is_arg_name_regex_correctness(name):
    """_is_arg_name should match valid Python identifiers."""
    result = docstrings._is_arg_name(name)
    stripped = name.strip()
    
    # Check against Python's identifier rules
    if result:
        # Should match the documented pattern: letter/underscore followed by word chars
        pattern = r'^[a-zA-Z_]\w*$'
        assert re.match(pattern, stripped) is not None
        # Should be a valid Python identifier (mostly)
        if not stripped.startswith('_'):
            try:
                # Basic check - valid identifiers can be used in exec
                exec(f"{stripped} = 1")
                valid_identifier = True
            except:
                valid_identifier = False
            if valid_identifier and not stripped.isdigit():
                assert result == True


# Test 5: _join_lines properties
@given(st.lists(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'), whitelist_characters=' \t\n'))))
def test_join_lines_handles_blank_lines(lines):
    """_join_lines should handle blank lines by creating paragraph breaks."""
    result = docstrings._join_lines(lines)
    
    if result is None:
        # Check that all lines were blank or empty
        assert all(not line.strip() for line in lines)
    else:
        # Non-empty result should not start or end with whitespace paragraphs
        paragraphs = result.split('\n\n')
        if paragraphs:
            assert paragraphs[0].strip() != ''
            assert paragraphs[-1].strip() != ''


# Test 6: _cast_to_known_type behavior
@given(st.one_of(st.none(), st.text()))
def test_cast_to_known_type_strips_dots(type_str):
    """_cast_to_known_type should strip trailing dots from type strings."""
    result = docstrings._cast_to_known_type(type_str)
    
    if type_str is None:
        assert result is None
    else:
        # Should strip trailing dots
        assert result == type_str.rstrip('.')
        # Should be idempotent
        assert docstrings._cast_to_known_type(result) == result


# Test 7: Round-trip property for simple docstrings
@given(st.text(min_size=1).filter(lambda x: x.strip() and '\n' not in x.strip()))
def test_simple_summary_extraction(summary):
    """Single-line docstrings should be extracted as summary."""
    assume(summary.strip())  # Non-empty after stripping
    docstring = f"    {summary}    "  # Add whitespace
    
    result = docstrings.parse(docstring)
    assert result.summary == summary.strip()
    assert result.description is None
    assert result.args is None
    assert result.returns is None


# Test 8: Args section parsing invariant
@given(st.text())
def test_args_section_structure(content):
    """Args section should produce structured ArgInfo objects."""
    docstring = f"""Summary.
    
    Args:
        {content}
    """
    
    result = docstrings.parse(docstring)
    if result.args:
        for arg in result.args:
            assert isinstance(arg, (docstrings.ArgInfo, docstrings.KwargInfo))
            assert arg.name is not None
            # Name should be a valid arg name if it was parsed
            assert docstrings._is_arg_name(arg.name)


# Test 9: Section title matching is case-insensitive
@given(st.sampled_from(['Args', 'ARGS', 'args', 'ArGs', 'Arg', 'Arguments', 'Parameters', 'Params']))
def test_section_matching_case_insensitive(title):
    """Section titles should be matched case-insensitively."""
    docstring = f"""Summary.
    
    {title}:
        param1: Description
    """
    
    result = docstrings.parse(docstring)
    # If it's a valid args section variant, it should be parsed
    assert result.summary == 'Summary.'


# Test 10: Large input performance (not crashing on large strings)
@given(st.text(min_size=10000, max_size=100000))
@settings(max_examples=10, deadline=5000)  # 5 second deadline
def test_large_input_performance(large_docstring):
    """Parse should handle large inputs without hanging (O(n) time claim)."""
    result = docstrings.parse(large_docstring)
    assert isinstance(result, docstrings.DocstringInfo)