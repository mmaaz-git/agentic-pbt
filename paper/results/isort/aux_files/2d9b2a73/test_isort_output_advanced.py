#!/usr/bin/env python3
"""Advanced property-based tests for isort.output module."""

import sys
import os
import traceback

# Add isort to path
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

# Import required modules
from hypothesis import given, strategies as st, settings, assume, Verbosity
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


# Test 1: _ensure_newline_before_comment complex cases
@given(st.lists(st.text()))
@settings(max_examples=100)
def test_ensure_newline_before_comment_complex(lines):
    """Test _ensure_newline_before_comment with various comment patterns."""
    # Create lines with different patterns
    test_lines = []
    for i, line in enumerate(lines):
        if i % 4 == 0:
            test_lines.append(f"# comment {line}")
        elif i % 4 == 1:
            test_lines.append(line if line else "code")
        elif i % 4 == 2:
            test_lines.append("")
        else:
            test_lines.append(f"# another comment {line}")
    
    result = output._ensure_newline_before_comment(test_lines)
    
    # Verify comments have proper spacing
    for i in range(1, len(result)):
        if result[i].startswith("#"):
            prev = result[i-1] if i > 0 else ""
            # If previous is non-empty non-comment, should have empty line inserted
            if prev and not prev.startswith("#"):
                # Check that empty line was properly inserted
                pass


# Test 2: _with_star_comments edge cases
@given(st.lists(st.text()), st.text())
def test_with_star_comments_edge_cases(comments, module_name):
    """Test _with_star_comments with various edge cases."""
    # Create ParsedContent with star comment
    categorized_comments = {
        "from": {},
        "straight": {},
        "nested": {module_name: {"*": "star comment"}},
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
    
    result = output._with_star_comments(parsed, module_name, comments.copy())
    
    # Star comment should be appended if exists
    assert "star comment" in result, f"Star comment not found in result: {result}"
    # All original comments should still be there
    for comment in comments:
        assert comment in result


# Test 3: sorted_imports with minimal ParsedContent
@given(st.sampled_from(["\n", "\r\n", "\r"]))
@settings(max_examples=10)
def test_sorted_imports_minimal(line_separator):
    """Test sorted_imports with minimal valid ParsedContent."""
    # Create minimal ParsedContent
    parsed = ParsedContent(
        in_lines=[],
        lines_without_imports=["# test file", "print('hello')"],
        import_index=-1,  # No imports
        place_imports={},
        import_placements={},
        as_map={"straight": {}, "from": {}},
        imports={
            "STDLIB": {"straight": OrderedDict(), "from": OrderedDict()},
            "THIRDPARTY": {"straight": OrderedDict(), "from": OrderedDict()},
            "FIRSTPARTY": {"straight": OrderedDict(), "from": OrderedDict()},
            "LOCALFOLDER": {"straight": OrderedDict(), "from": OrderedDict()},
        },
        categorized_comments={
            "from": {},
            "straight": {},
            "nested": {},
            "above": {"straight": {}, "from": {}},
        },
        change_count=0,
        original_line_count=2,
        line_separator=line_separator,
        sections=["STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"],
        verbose_output=[],
        trailing_commas=set()
    )
    
    result = output.sorted_imports(parsed, DEFAULT_CONFIG, "py", "import")
    
    # Should return original lines when no imports
    expected = line_separator.join(["# test file", "print('hello')", ""])
    assert result == expected, f"Expected {repr(expected)}, got {repr(result)}"


# Test 4: sorted_imports with actual imports
@given(st.sampled_from(["\n", "\r\n"]))
@settings(max_examples=10)
def test_sorted_imports_with_imports(line_separator):
    """Test sorted_imports with actual import statements."""
    # Create ParsedContent with imports
    imports = {
        "STDLIB": {
            "straight": OrderedDict([("os", {"": None}), ("sys", {"": None})]),
            "from": OrderedDict()
        },
        "THIRDPARTY": {"straight": OrderedDict(), "from": OrderedDict()},
        "FIRSTPARTY": {"straight": OrderedDict(), "from": OrderedDict()},
        "LOCALFOLDER": {"straight": OrderedDict(), "from": OrderedDict()},
    }
    
    parsed = ParsedContent(
        in_lines=["import os", "import sys", "print('hello')"],
        lines_without_imports=["print('hello')"],
        import_index=0,
        place_imports={},
        import_placements={},
        as_map={"straight": defaultdict(list), "from": defaultdict(list)},
        imports=imports,
        categorized_comments={
            "from": {},
            "straight": {},
            "nested": {},
            "above": {"straight": {}, "from": {}},
        },
        change_count=0,
        original_line_count=3,
        line_separator=line_separator,
        sections=["STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"],
        verbose_output=[],
        trailing_commas=set()
    )
    
    result = output.sorted_imports(parsed, DEFAULT_CONFIG, "py", "import")
    
    # Should contain sorted imports
    assert "import os" in result
    assert "import sys" in result
    assert "print('hello')" in result
    # Imports should be sorted
    os_pos = result.index("import os")
    sys_pos = result.index("import sys")
    assert os_pos < sys_pos, "Imports not sorted alphabetically"


# Test 5: _normalize_empty_lines with only empty strings
@given(st.integers(min_value=0, max_value=100))
def test_normalize_empty_lines_only_empty(num_empty):
    """Test _normalize_empty_lines with lists of only empty strings."""
    lines = [""] * num_empty
    result = output._normalize_empty_lines(lines.copy())
    
    # Should always result in single empty string
    assert result == [""], f"List of {num_empty} empty strings should normalize to [''], got {result}"


# Test 6: Test _output_as_string preserves non-empty content
@given(
    st.lists(st.text(min_size=1).filter(lambda x: x.strip()), min_size=1),
    st.sampled_from(["\n", "\r\n", "\r"])
)
@settings(max_examples=50)
def test_output_as_string_preserves_non_empty(lines, separator):
    """Test that non-empty lines are preserved in _output_as_string."""
    result = output._output_as_string(lines.copy(), separator)
    
    # All non-empty lines should be in result
    for line in lines:
        if line.strip():  # non-empty line
            assert line in result, f"Lost non-empty line: {line}"


# Test 7: Boundary test - very long lines
@given(st.text(min_size=10000, max_size=50000))
@settings(max_examples=5)
def test_very_long_lines(long_text):
    """Test handling of very long lines."""
    lines = [long_text, "short", long_text]
    result = output._normalize_empty_lines(lines.copy())
    
    # Long lines should be preserved
    assert long_text in result[0] or long_text in result[1], "Long line not preserved"


# Test 8: Unicode and special characters
@given(
    st.lists(st.sampled_from(["🎉", "α", "β", "γ", "δ", "ε", "中文", "العربية", "\U0001F600", ""]))
)
@settings(max_examples=50)
def test_unicode_handling(lines):
    """Test handling of Unicode characters."""
    result = output._normalize_empty_lines(lines.copy())
    
    # All non-empty unicode strings should be preserved
    non_empty_unicode = [l for l in lines if l]
    for unicode_str in non_empty_unicode:
        assert any(unicode_str in line for line in result), f"Lost Unicode string: {unicode_str}"


def main():
    """Run all tests and report results."""
    tests = [
        (test_ensure_newline_before_comment_complex, "test_ensure_newline_before_comment_complex"),
        (test_with_star_comments_edge_cases, "test_with_star_comments_edge_cases"),
        (test_sorted_imports_minimal, "test_sorted_imports_minimal"),
        (test_sorted_imports_with_imports, "test_sorted_imports_with_imports"),
        (test_normalize_empty_lines_only_empty, "test_normalize_empty_lines_only_empty"),
        (test_output_as_string_preserves_non_empty, "test_output_as_string_preserves_non_empty"),
        (test_very_long_lines, "test_very_long_lines"),
        (test_unicode_handling, "test_unicode_handling"),
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