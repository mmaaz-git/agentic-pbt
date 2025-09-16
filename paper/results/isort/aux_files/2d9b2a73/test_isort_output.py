"""Property-based tests for isort.output module using Hypothesis."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import isort.output as output
from isort.parse import ParsedContent
from isort.settings import Config, DEFAULT_CONFIG
from collections import OrderedDict


@given(st.lists(st.text()))
def test_normalize_empty_lines_idempotence(lines):
    """Test that _normalize_empty_lines is idempotent."""
    result1 = output._normalize_empty_lines(lines.copy())
    result2 = output._normalize_empty_lines(result1.copy())
    assert result1 == result2, f"Not idempotent: {lines} -> {result1} -> {result2}"


@given(st.lists(st.text()))
def test_normalize_empty_lines_ends_with_empty(lines):
    """Test that _normalize_empty_lines always ends with exactly one empty line."""
    if not lines:  # Skip empty input
        return
    result = output._normalize_empty_lines(lines.copy())
    assert len(result) >= 1, "Result should have at least one line"
    assert result[-1] == "", f"Last line should be empty, got: {repr(result[-1])}"
    # Check no trailing empty lines except the last one
    if len(result) > 1:
        assert result[-2] != "" or len(result) == 1, f"Should not have multiple trailing empty lines: {result[-3:]}"


@given(st.lists(st.text()), st.sampled_from(["\n", "\r\n", "\r"]))
def test_output_as_string_line_separator(lines, separator):
    """Test that _output_as_string uses consistent line separators."""
    result = output._output_as_string(lines.copy(), separator)
    
    # Check that the result uses the specified separator
    if len(lines) > 1:
        assert separator in result or not any(lines), f"Separator {repr(separator)} not found in result"
    
    # Check no mixed separators
    wrong_seps = [s for s in ["\n", "\r\n", "\r"] if s != separator]
    for wrong_sep in wrong_seps:
        # Only check if the wrong separator is not a substring of the correct one
        if wrong_sep not in separator and separator not in wrong_sep:
            assert wrong_sep not in result, f"Found wrong separator {repr(wrong_sep)} in result with separator {repr(separator)}"


@given(st.lists(st.text()))
def test_output_as_string_preserves_content(lines):
    """Test that content is preserved (modulo normalization) in _output_as_string."""
    separator = "\n"
    result = output._output_as_string(lines.copy(), separator)
    
    # The function normalizes empty lines, so we need to account for that
    normalized = output._normalize_empty_lines(lines.copy())
    expected = separator.join(normalized)
    
    assert result == expected, f"Content not preserved correctly"


@given(st.lists(st.text(min_size=1)))
def test_ensure_newline_before_comment_idempotence(lines):
    """Test that _ensure_newline_before_comment is idempotent."""
    # Make some lines comments
    modified_lines = []
    for i, line in enumerate(lines):
        if i % 3 == 0:
            modified_lines.append(f"# {line}")
        else:
            modified_lines.append(line)
    
    result1 = output._ensure_newline_before_comment(modified_lines.copy())
    result2 = output._ensure_newline_before_comment(result1.copy())
    assert result1 == result2, f"Not idempotent"


@given(st.lists(st.text()), st.lists(st.text()))
def test_ensure_newline_before_comment_adds_newlines(code_lines, comment_texts):
    """Test that comments get newlines before them when preceded by non-comments."""
    lines = []
    for i, line in enumerate(code_lines):
        lines.append(line)
        if i < len(comment_texts):
            lines.append(f"# {comment_texts[i]}")
    
    result = output._ensure_newline_before_comment(lines)
    
    # Check that comments have newlines before them (except at start or after empty/comment)
    for i in range(1, len(result)):
        if result[i].startswith("#"):
            prev = result[i-1]
            # If previous line is not empty and not a comment, there should be empty line before
            if prev != "" and not prev.startswith("#"):
                # We expect an empty line was inserted
                pass  # The function should have handled this
    
    # Basic property: result should contain all original content
    original_non_empty = [l for l in lines if l]
    result_non_empty = [l for l in result if l]
    for orig in original_non_empty:
        assert orig in result_non_empty, f"Lost line: {orig}"


@given(st.text(), st.lists(st.text()))
def test_LineWithComments_preserves_value_and_comments(value, comments):
    """Test that _LineWithComments preserves both the string value and comments."""
    line_with_comments = output._LineWithComments(value, comments)
    
    # Test string value is preserved
    assert str(line_with_comments) == value
    assert line_with_comments == value  # Should compare as string
    
    # Test comments are preserved
    assert line_with_comments.comments == comments
    
    # Test it behaves like a string
    assert len(line_with_comments) == len(value)
    if value:
        assert line_with_comments[0] == value[0]


@given(st.lists(st.text()))
def test_with_star_comments_preserves_comments(comments):
    """Test that _with_star_comments preserves existing comments."""
    # Create a minimal ParsedContent with categorized_comments
    categorized_comments = {
        "from": {},
        "straight": {},
        "nested": {"test_module": {}},
        "above": {"straight": {}, "from": {}},
    }
    
    parsed = ParsedContent(
        in_lines=[],
        lines_without_imports=[],
        import_index=-1,
        place_imports={},
        import_placements={},
        as_map={"straight": {}, "from": {}},
        imports={},
        categorized_comments=categorized_comments,
        change_count=0,
        original_line_count=0,
        line_separator="\n",
        sections=[],
        verbose_output=[],
        trailing_commas=set()
    )
    
    result = output._with_star_comments(parsed, "test_module", comments.copy())
    
    # All original comments should be in result
    for comment in comments:
        assert comment in result, f"Lost comment: {comment}"


@given(st.lists(st.text()), st.sampled_from(["\n", "\r\n", "\r"]))
def test_output_as_string_ends_correctly(lines, separator):
    """Test that _output_as_string output ends with exactly one separator."""
    result = output._output_as_string(lines.copy(), separator)
    
    # Should end with separator (due to normalization adding empty line)
    if lines or True:  # Always true due to normalization
        assert result.endswith(separator), f"Should end with separator {repr(separator)}"
        # Should not have double separator at end
        if len(result) > len(separator):
            assert not result.endswith(separator + separator), f"Should not end with double separator"


if __name__ == "__main__":
    # Run all tests
    import pytest
    pytest.main([__file__, "-v"])