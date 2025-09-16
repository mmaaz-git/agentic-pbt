#!/usr/bin/env python3
"""Edge case tests for isort.output module to find potential bugs."""

import sys
import os
import traceback

# Add isort to path
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

# Import required modules
from hypothesis import given, strategies as st, settings, assume, Verbosity, example
import isort.output as output
from isort.parse import ParsedContent
from isort.settings import Config, DEFAULT_CONFIG
from collections import OrderedDict, defaultdict


def run_test(test_func, test_name):
    """Run a single test and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print('='*60)
    
    try:
        test_func()
        print(f"✓ {test_name} PASSED")
        return True
    except Exception as e:
        print(f"✗ {test_name} FAILED")
        print(f"Error: {e}")
        traceback.print_exc()
        return False


# Test 1: _normalize_empty_lines with mixed empty and whitespace-only lines
@given(st.lists(st.sampled_from(["", " ", "  ", "\t", "\n", "\r", "  \t  ", "text", "  text  "])))
@settings(max_examples=100)
def test_normalize_empty_lines_whitespace(lines):
    """Test _normalize_empty_lines with various whitespace patterns."""
    result = output._normalize_empty_lines(lines.copy())
    
    # Check idempotence
    result2 = output._normalize_empty_lines(result.copy())
    assert result == result2, f"Not idempotent with whitespace"
    
    # Should end with empty line
    assert result[-1] == "", f"Should end with empty line"
    
    # No multiple trailing empty lines
    if len(result) > 1:
        # Check that we don't have multiple trailing empties
        trailing_empties = 0
        for i in range(len(result) - 1, -1, -1):
            if result[i].strip() == "":
                trailing_empties += 1
            else:
                break
        assert trailing_empties == 1, f"Should have exactly 1 trailing empty, got {trailing_empties}"


# Test 2: Line separator edge cases
@given(
    st.lists(st.text(alphabet=st.characters(blacklist_characters="\r\n"))),
    st.sampled_from(["\n", "\r\n", "\r", "\n\r"])  # Including non-standard \n\r
)
@settings(max_examples=50)
def test_output_as_string_unusual_separators(lines, separator):
    """Test _output_as_string with unusual separator patterns."""
    if separator == "\n\r":  # This is non-standard but let's test it
        # The function should still work
        result = output._output_as_string(lines.copy(), separator)
        # Basic check - should use the separator
        if len(lines) > 1 and any(lines):
            assert separator in result or all(not l for l in lines)


# Test 3: Empty and single-line edge cases
def test_edge_case_empty_variations():
    """Test various edge cases with empty inputs."""
    # Test 1: Completely empty
    assert output._normalize_empty_lines([]) == [""]
    
    # Test 2: Single empty string
    assert output._normalize_empty_lines([""]) == [""]
    
    # Test 3: Multiple empty strings
    assert output._normalize_empty_lines(["", "", ""]) == [""]
    
    # Test 4: Whitespace that looks empty
    result = output._normalize_empty_lines(["   ", "\t", "  "])
    assert result[-1] == ""
    assert all(r == "   " or r == "\t" or r == "  " or r == "" for r in result)


# Test 4: _LineWithComments with empty values
@given(
    st.one_of(st.just(""), st.text()),
    st.one_of(st.just([]), st.lists(st.text()))
)
@settings(max_examples=100)
def test_LineWithComments_empty_edge_cases(value, comments):
    """Test _LineWithComments with empty strings and lists."""
    line = output._LineWithComments(value, comments)
    
    # Empty string should work
    assert str(line) == value
    assert line.comments == comments
    
    # Test string operations on empty
    if value == "":
        assert len(line) == 0
        assert line == ""
        assert not line  # Empty string is falsy


# Test 5: Comments with special characters
@given(st.lists(st.text(alphabet=st.characters())))
@settings(max_examples=50)
def test_ensure_newline_before_comment_special_chars(lines):
    """Test _ensure_newline_before_comment with special characters."""
    # Add some lines that start with # but contain special chars
    test_lines = []
    for i, line in enumerate(lines):
        if i % 3 == 0:
            test_lines.append(f"#\x00\x01\x02{line}")  # Comment with null chars
        elif i % 3 == 1:
            test_lines.append(line)
        else:
            test_lines.append(f"# {line}")
    
    result = output._ensure_newline_before_comment(test_lines)
    
    # Should be idempotent even with special chars
    result2 = output._ensure_newline_before_comment(result.copy())
    assert result == result2


# Test 6: Test interaction between normalization and output
@given(
    st.lists(st.text()),
    st.sampled_from(["\n", "\r\n", "\r"])
)
@settings(max_examples=50)
def test_normalize_then_output(lines, separator):
    """Test that normalize + output work together correctly."""
    # First normalize
    normalized = output._normalize_empty_lines(lines.copy())
    # Then output
    result = output._output_as_string(lines.copy(), separator)
    
    # The output function calls normalize internally, so result should be consistent
    expected = separator.join(normalized)
    assert result == expected


# Test 7: Large number of empty lines
@given(st.integers(min_value=100, max_value=1000))
@settings(max_examples=10)
def test_many_empty_lines(n):
    """Test handling of many consecutive empty lines."""
    lines = [""] * n
    result = output._normalize_empty_lines(lines)
    assert result == [""], f"Many empty lines should collapse to single empty"
    
    # Also test with some content
    lines2 = ["content"] + [""] * n
    result2 = output._normalize_empty_lines(lines2)
    assert result2 == ["content", ""], f"Should remove trailing empties except one"


# Test 8: Test actual bug-prone scenario - trailing whitespace
def test_trailing_whitespace_normalization():
    """Test normalization of lines with trailing whitespace."""
    lines = ["import os  ", "import sys\t", "", "  ", ""]
    result = output._normalize_empty_lines(lines)
    
    # Trailing whitespace in non-empty lines should be preserved
    assert "import os  " in result or "import os" in result
    assert "import sys\t" in result or "import sys" in result
    
    # But empty lines should be normalized
    assert result[-1] == ""


# Test 9: Regression test for potential off-by-one errors
def test_off_by_one_scenarios():
    """Test potential off-by-one errors in list operations."""
    # Single item
    assert output._normalize_empty_lines(["x"]) == ["x", ""]
    
    # Two items, second empty
    assert output._normalize_empty_lines(["x", ""]) == ["x", ""]
    
    # Empty, then content
    assert output._normalize_empty_lines(["", "x"]) == ["", "x", ""]
    
    # Content, empty, content
    result = output._normalize_empty_lines(["x", "", "y"])
    assert "x" in result and "y" in result
    assert result[-1] == ""


def main():
    """Run all tests and report results."""
    tests = [
        (test_normalize_empty_lines_whitespace, "test_normalize_empty_lines_whitespace"),
        (test_output_as_string_unusual_separators, "test_output_as_string_unusual_separators"),
        (test_edge_case_empty_variations, "test_edge_case_empty_variations"),
        (test_LineWithComments_empty_edge_cases, "test_LineWithComments_empty_edge_cases"),
        (test_ensure_newline_before_comment_special_chars, "test_ensure_newline_before_comment_special_chars"),
        (test_normalize_then_output, "test_normalize_then_output"),
        (test_many_empty_lines, "test_many_empty_lines"),
        (test_trailing_whitespace_normalization, "test_trailing_whitespace_normalization"),
        (test_off_by_one_scenarios, "test_off_by_one_scenarios"),
    ]
    
    passed = 0
    failed = 0
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print('='*60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)