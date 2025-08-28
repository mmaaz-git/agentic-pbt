#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import re
from jurigged.codetools import (
    splitlines, substantial, analyze_split, 
    Correspondence, Info, Extent, use_info
)


# Test 1: splitlines removes empty last line
@given(st.text())
def test_splitlines_removes_empty_last_line(s):
    """Property: If input ends with a newline, splitlines removes the resulting empty last line."""
    from ast import _splitlines_no_ff as _splitlines
    
    result = splitlines(s)
    raw_lines = _splitlines(s)
    
    # The function removes the last line if it's empty
    if len(raw_lines) > 0 and raw_lines[-1] == "":
        assert result == raw_lines[:-1]
    else:
        assert result == raw_lines
    
    # Result should never end with an empty string
    assert not (result and result[-1] == "")


# Test 2: substantial function correctly identifies non-substantial lines
@given(st.text(alphabet=" \t#\n", min_size=0))
def test_substantial_whitespace_and_comments(s):
    """Property: Lines with only spaces, comments, and newlines are not substantial."""
    # According to the regex: r" *(#.*)?\n?"
    # This matches: any spaces, optional comment starting with #, optional newline
    
    is_substantial = substantial(s)
    
    # Check if the string matches the "non-substantial" pattern
    matches_pattern = re.fullmatch(r" *(#.*)?\n?", s) is not None
    
    # The function returns NOT matches_pattern
    assert is_substantial == (not matches_pattern)


# Test 3: substantial function with mixed content
@given(st.text())
def test_substantial_general(s):
    """Property: substantial returns False iff the line matches the whitespace/comment pattern."""
    result = substantial(s)
    pattern_match = re.fullmatch(r" *(#.*)?\n?", s)
    assert result == (pattern_match is None)


# Test 4: analyze_split round-trip property
@given(st.text())
def test_analyze_split_concatenation(s):
    """Property: Concatenating the three parts from analyze_split preserves content."""
    left, middle, right = analyze_split(s)
    
    # The original string after splitlines processing
    lines = splitlines(s)
    original = "".join(lines)
    
    # The concatenation of the three parts
    reconstructed = left + middle + right
    
    # They should be equal
    assert reconstructed == original


# Test 5: analyze_split left contains substantial lines
@given(st.text())
def test_analyze_split_left_contains_substantial(s):
    """Property: The 'left' part contains all lines up to and including the last substantial line."""
    left, middle, right = analyze_split(s)
    
    if left:
        # If left is non-empty, it should end with a substantial line
        # or be the only content
        lines_in_left = splitlines(left)
        if lines_in_left:
            # At least one line in left should be substantial
            assert any(substantial(line) for line in lines_in_left)


# Test 6: Correspondence.fitness returns expected tuple values
@given(st.booleans(), st.booleans())
def test_correspondence_fitness(corresponds, changed):
    """Property: fitness returns (0|1, 0|1) based on corresponds and changed flags."""
    # Create a minimal Correspondence object
    corr = Correspondence(
        original=None,
        new=None,
        corresponds=corresponds,
        changed=changed
    )
    
    fitness = corr.fitness()
    
    # First element should be 1 if corresponds is True, 0 otherwise
    assert fitness[0] == int(corresponds)
    
    # Second element should be 0 if changed is True, 1 otherwise
    assert fitness[1] == (1 - int(changed))
    
    # Both elements should be 0 or 1
    assert fitness[0] in (0, 1)
    assert fitness[1] in (0, 1)


# Test 7: Info.get_segment for single-line segments (FIXED)
@given(
    st.lists(st.text(min_size=1), min_size=5, max_size=20),
    st.integers(min_value=0, max_value=4),
    st.integers(min_value=0, max_value=10),
    st.integers(min_value=0, max_value=10)
)
def test_info_get_segment_single_line(lines, line_idx, start_col, length):
    """Property: For single-line segments, get_segment returns the exact substring."""
    assume(line_idx < len(lines))
    assume(start_col <= len(lines[line_idx]))
    
    end_col = min(start_col + length, len(lines[line_idx]))
    
    # Create Info object with our lines
    info = Info(
        filename="test.py",
        module_name="test",
        source="\n".join(lines),
        lines=lines
    )
    
    # Need to set up the context for Extent to work properly
    with use_info(
        filename="test.py",
        module_name="test",
        source="\n".join(lines),
        lines=lines
    ):
        # Create extent for single line
        ext = Extent(
            lineno=line_idx + 1,  # 1-based
            col_offset=start_col,
            end_lineno=line_idx + 1,  # same line
            end_col_offset=end_col
        )
        
        result = info.get_segment(ext)
        
        # Should match the substring
        expected = lines[line_idx].encode()[start_col:end_col].decode()
        assert result == expected


# Test 8: Correspondence valid/invalid factory methods
@given(st.booleans())
def test_correspondence_factory_methods(changed_flag):
    """Property: valid() creates corresponds=True, invalid() creates corresponds=False."""
    # Test valid factory
    valid_corr = Correspondence.valid(
        original=None,
        new=None,
        changed=changed_flag
    )
    assert valid_corr.corresponds is True
    assert valid_corr.changed == changed_flag
    
    # Test invalid factory
    invalid_corr = Correspondence.invalid(
        original=None,
        new=None
    )
    assert invalid_corr.corresponds is False
    assert invalid_corr.changed is False


# Test 9: Testing Extent creation without context
@given(st.integers(min_value=1, max_value=100), st.integers(min_value=0, max_value=100))
def test_extent_creation_with_explicit_filename(lineno, col_offset):
    """Property: Extent can be created with explicit filename."""
    ext = Extent(
        lineno=lineno,
        col_offset=col_offset,
        end_lineno=lineno,
        end_col_offset=col_offset + 10,
        filename="explicit.py"
    )
    assert ext.filename == "explicit.py"
    assert ext.lineno == lineno
    assert ext.col_offset == col_offset


# Test 10: More complex analyze_split property
@given(st.text())
def test_analyze_split_middle_has_no_substantial(s):
    """Property: The middle part should contain no substantial lines."""
    left, middle, right = analyze_split(s)
    
    if middle:
        # Middle should not contain any substantial lines
        lines_in_middle = splitlines(middle)
        for line in lines_in_middle:
            if line:  # Skip empty lines
                assert not substantial(line)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])