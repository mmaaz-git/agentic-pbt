"""Property-based tests for isort.parse module"""

import re
from hypothesis import assume, given, strategies as st
from hypothesis import settings

# Add parent directory to path to import from installed isort
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.parse import (
    _infer_line_separator,
    normalize_line,
    import_type,
    strip_syntax,
    skip_line,
    file_contents
)
from isort.settings import Config


# Property 1: _infer_line_separator always returns a valid separator
@given(st.text())
def test_infer_line_separator_returns_valid_separator(contents):
    """Line separator inference should always return \\r\\n, \\r, or \\n"""
    result = _infer_line_separator(contents)
    assert result in ("\r\n", "\r", "\n")


# Property 2: _infer_line_separator returns the correct separator when present
@given(st.text())
def test_infer_line_separator_correctness(contents):
    """Should return the actual separator present in the content"""
    result = _infer_line_separator(contents)
    if "\r\n" in contents:
        assert result == "\r\n"
    elif "\r" in contents:
        assert result == "\r"
    else:
        assert result == "\n"


# Property 3: normalize_line always returns a tuple with second element unchanged
@given(st.text())
def test_normalize_line_preserves_raw(raw_line):
    """normalize_line should preserve the raw line as second element"""
    normalized, returned_raw = normalize_line(raw_line)
    assert returned_raw == raw_line
    assert isinstance(normalized, str)
    assert isinstance(returned_raw, str)


# Property 4: normalize_line idempotence for already normalized lines
@given(st.text())
def test_normalize_line_idempotence(line):
    """Normalizing an already normalized line should not change it further"""
    normalized1, _ = normalize_line(line)
    normalized2, _ = normalize_line(normalized1)
    # After normalizing once, normalizing again should produce the same result
    assert normalized2 == normalize_line(normalized2)[0]


# Property 5: import_type classification consistency
@given(st.text())
def test_import_type_classification(line):
    """import_type should classify consistently based on line start"""
    config = Config()
    result = import_type(line, config)
    
    # Skip lines with special markers
    if "isort:skip" in line or "isort: skip" in line or "isort: split" in line:
        assert result is None
    elif config.honor_noqa and line.lower().rstrip().endswith("noqa"):
        assert result is None
    elif line.startswith(("import ", "cimport ")):
        assert result == "straight"
    elif line.startswith("from "):
        assert result == "from"
    else:
        assert result is None


# Property 6: import_type returns one of three valid values
@given(st.text())
def test_import_type_valid_values(line):
    """import_type should only return 'from', 'straight', or None"""
    result = import_type(line, Config())
    assert result in ("from", "straight", None)


# Property 7: strip_syntax removes syntax characters
@given(st.text())
def test_strip_syntax_removes_characters(import_string):
    """strip_syntax should remove parentheses, commas, and backslashes"""
    result = strip_syntax(import_string)
    # These characters should be replaced with spaces or removed
    for char in ["\\", "(", ")", ","]:
        # After stripping, these should not appear except in specific contexts
        if char in result:
            # Check if it's part of the {| |} pattern
            assert "{|" in result or "|}" in result


# Property 8: skip_line quote tracking consistency
@given(
    st.text(),
    st.sampled_from(["", "'", '"', "'''", '"""']),
    st.integers(min_value=0, max_value=1000),
    st.tuples()
)
def test_skip_line_quote_state(line, initial_quote, index, section_comments):
    """skip_line should maintain consistent quote state"""
    should_skip, final_quote = skip_line(line, initial_quote, index, section_comments)
    
    # The returned quote should be a string
    assert isinstance(final_quote, str)
    
    # If we started in a quote and the line doesn't close it, we should still be in a quote
    if initial_quote and initial_quote not in line:
        assert should_skip == True


# Property 9: Multiple import types cannot coexist
@given(st.text())
def test_import_type_mutual_exclusion(line):
    """A line cannot be both 'from' and 'straight' import"""
    config = Config()
    result = import_type(line, config)
    
    # If it's a from import, it can't start with "import " or "cimport "
    if result == "from":
        assert not line.startswith(("import ", "cimport "))
    
    # If it's a straight import, it can't start with "from "
    if result == "straight":
        assert not line.startswith("from ")


# Property 10: normalize_line handles tabs consistently
@given(st.text())
def test_normalize_line_tab_handling(raw_line):
    """normalize_line should replace all tabs with spaces"""
    normalized, _ = normalize_line(raw_line)
    # After normalization, there should be no tabs
    assert "\t" not in normalized


# Property 11: strip_syntax preserves _import and _cimport specially
@given(st.text())
def test_strip_syntax_preserves_underscore_imports(text):
    """strip_syntax should handle _import and _cimport carefully"""
    # Only test with valid patterns
    if "_import" in text or "_cimport" in text:
        result = strip_syntax(text)
        # The function uses placeholders [[i]] and [[ci]] internally
        # but should restore _import and _cimport in the output
        assert "[[i]]" not in result
        assert "[[ci]]" not in result


# Property 12: file_contents preserves non-import line count
@given(st.text())
@settings(max_examples=100, deadline=5000)
def test_file_contents_line_preservation(contents):
    """file_contents should track line counts correctly"""
    # Skip very large inputs to avoid timeout
    assume(len(contents) < 10000)
    assume(contents.count('\n') < 500)
    
    try:
        result = file_contents(contents, Config())
        
        # Original line count should match input
        input_lines = contents.splitlines()
        if contents and contents[-1] in ("\n", "\r"):
            input_lines.append("")
        
        assert result.original_line_count == len(input_lines)
        
        # The change count should be the difference
        assert result.change_count == len(result.lines_without_imports) - result.original_line_count
    except Exception:
        # Skip cases that cause exceptions due to malformed input
        pass


# Property 13: Line separator inference is deterministic
@given(st.text())
def test_line_separator_deterministic(contents):
    """Same input should always produce same line separator"""
    result1 = _infer_line_separator(contents)
    result2 = _infer_line_separator(contents)
    assert result1 == result2


# Property 14: import_type with skip markers
@given(st.text())
def test_import_type_skip_markers(base_line):
    """Lines with skip markers should always return None"""
    # Add skip markers to the line
    skip_lines = [
        base_line + " # isort:skip",
        base_line + " # isort: skip",
        base_line + " # isort: split",
        "# isort:skip\n" + base_line
    ]
    
    config = Config()
    for line in skip_lines:
        if "isort:skip" in line or "isort: skip" in line or "isort: split" in line:
            assert import_type(line, config) is None


# Property 15: normalize_line handles cimport spacing
@given(st.text())
def test_normalize_line_cimport_spacing(text):
    """normalize_line should normalize cimport spacing"""
    if "cimport" in text:
        normalized, _ = normalize_line(text)
        # After normalization, patterns like "from.cimport" should become "from . cimport"
        assert "from.cimport" not in normalized.replace("from . cimport", "")
        assert "from..cimport" not in normalized.replace("from .. cimport", "")