#!/usr/bin/env python3
"""Run property-based tests for isort.output module."""

import sys
import os
import traceback

# Add isort to path
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

# Import required modules
from hypothesis import given, strategies as st, settings, assume, find, Verbosity
import isort.output as output
from isort.parse import ParsedContent
from isort.settings import Config, DEFAULT_CONFIG
from collections import OrderedDict


def run_test(test_func, test_name):
    """Run a single test and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print('='*60)
    
    try:
        # Try to find a failing example
        test_func()
        print(f"✓ {test_name} PASSED")
        return True
    except Exception as e:
        print(f"✗ {test_name} FAILED")
        print(f"Error: {e}")
        traceback.print_exc()
        return False


# Test 1: _normalize_empty_lines idempotence
@given(st.lists(st.text()))
@settings(max_examples=100, verbosity=Verbosity.verbose)
def test_normalize_empty_lines_idempotence(lines):
    """Test that _normalize_empty_lines is idempotent."""
    result1 = output._normalize_empty_lines(lines.copy())
    result2 = output._normalize_empty_lines(result1.copy())
    assert result1 == result2, f"Not idempotent: {lines} -> {result1} -> {result2}"


# Test 2: _normalize_empty_lines ends with empty
@given(st.lists(st.text()))
@settings(max_examples=100)
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


# Test 3: _output_as_string line separator
@given(st.lists(st.text()), st.sampled_from(["\n", "\r\n", "\r"]))
@settings(max_examples=100)
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


# Test 4: _LineWithComments preservation
@given(st.text(), st.lists(st.text()))
@settings(max_examples=100)
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


# Test 5: Specific edge case - empty list normalization
def test_empty_list_normalization():
    """Test empty list handling in _normalize_empty_lines."""
    result = output._normalize_empty_lines([])
    assert result == [""], f"Empty list should become single empty string, got: {result}"


# Test 6: Multiple trailing empty lines
def test_multiple_trailing_empty_normalization():
    """Test handling of multiple trailing empty lines."""
    lines = ["import os", "", "", ""]
    result = output._normalize_empty_lines(lines.copy())
    assert result[-1] == "", "Should end with empty line"
    assert result[-2] != "" if len(result) > 1 else True, f"Should not have multiple trailing empties: {result}"


def main():
    """Run all tests and report results."""
    tests = [
        (test_normalize_empty_lines_idempotence, "test_normalize_empty_lines_idempotence"),
        (test_normalize_empty_lines_ends_with_empty, "test_normalize_empty_lines_ends_with_empty"),
        (test_output_as_string_line_separator, "test_output_as_string_line_separator"),
        (test_LineWithComments_preserves_value_and_comments, "test_LineWithComments_preserves_value_and_comments"),
        (test_empty_list_normalization, "test_empty_list_normalization"),
        (test_multiple_trailing_empty_normalization, "test_multiple_trailing_empty_normalization"),
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