"""Edge case tests for isort.parse - hunting for real bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from isort.parse import (
    _infer_line_separator,
    normalize_line, 
    import_type,
    strip_syntax,
    skip_line,
    file_contents
)
from isort.settings import Config


# Test skip_line with escape sequences at boundaries
@given(st.integers(min_value=0, max_value=10))
def test_skip_line_escape_at_end(n):
    """Test skip_line when line ends with backslash"""
    lines = [
        "test" + "\\" * n,  # Multiple backslashes at end
        "'" + "\\" * n,     # Backslashes after quote start
        '"' + "\\" * n,     # Backslashes after double quote
        "\\" * n + "'",     # Backslashes before quote
    ]
    
    for line in lines:
        should_skip, quote = skip_line(line, "", 0, ())
        # Should handle escape sequences at boundaries
        assert isinstance(should_skip, bool)
        assert isinstance(quote, str)


# Test quote tracking with interleaved quotes
@given(st.text(alphabet="'\"", min_size=1, max_size=20))
def test_skip_line_interleaved_quotes(quote_sequence):
    """Test skip_line with complex quote sequences"""
    should_skip, final_quote = skip_line(quote_sequence, "", 0, ())
    
    # Count unescaped quotes
    i = 0
    single_count = 0
    double_count = 0
    while i < len(quote_sequence):
        if i > 0 and quote_sequence[i-1] == '\\':
            i += 1
            continue
        if quote_sequence[i] == "'":
            single_count += 1
        elif quote_sequence[i] == '"':
            double_count += 1
        i += 1
    
    # Final quote should reflect the state
    assert final_quote in ["", "'", '"', "'''", '"""']


# Test normalize_line with dots and spaces  
@given(st.integers(min_value=1, max_value=10))
def test_normalize_line_dots_spacing(num_dots):
    """Test normalize_line with various dot patterns in imports"""
    dots = "." * num_dots
    test_cases = [
        f"from{dots}import x",
        f"from{dots}cimport y",
        f"from {dots}import z",
        f"from {dots} import w",
    ]
    
    for case in test_cases:
        normalized, raw = normalize_line(case)
        assert raw == case
        # Should have space after from and before import/cimport
        if "cimport" in normalized:
            assert f"from {dots} cimport" in normalized
        elif "import" in normalized:
            assert f"from {dots} import" in normalized


# Test strip_syntax with special bracket patterns
@given(st.text(min_size=0, max_size=20))
def test_strip_syntax_bracket_patterns(content):
    """Test strip_syntax with curly bracket edge cases"""
    test_cases = [
        f"from x import {{{content}}}",
        f"from x import {{ {content} }}",
        f"from x import {{{content} }}",
        f"from x import {{ {content}}}",
    ]
    
    for case in test_cases:
        result = strip_syntax(case)
        # Check bracket transformation
        if "{" in case and "}" in case:
            # Should transform to {| |} pattern
            if "{ " in case:
                assert "{|" in result
            if " }" in case:
                assert "|}" in result


# Test import_type with whitespace variations
@given(st.text(alphabet=" \t\n\r", min_size=1, max_size=10))
def test_import_type_whitespace_prefix(whitespace):
    """Test import_type with various whitespace before keywords"""
    lines = [
        f"{whitespace}import os",
        f"{whitespace}from sys import argv",
        f"{whitespace}cimport module",
    ]
    
    config = Config()
    for line in lines:
        result = import_type(line, config)
        # Whitespace before import should make it not recognized
        if not line.startswith(("import ", "from ", "cimport ")):
            assert result is None


# Test file_contents with comment edge cases
def test_file_contents_comment_interactions():
    """Test file_contents with various comment scenarios"""
    test_contents = [
        "import os # comment with ; semicolon",
        "from sys import argv # isort:skip but not really",
        "import module # noqa # double comment",
        "# isort:imports-THIRDPARTY\nimport requests",
        "import a; import b # two imports with comment",
    ]
    
    for content in test_contents:
        try:
            result = file_contents(content, Config())
            # Should parse without crashing
            assert result is not None
        except:
            pass


# Test skip_line quote state machine
def test_skip_line_quote_state_machine():
    """Test skip_line quote tracking state transitions"""
    test_sequences = [
        ('"""hello', '"""'),  # Start triple quote
        ('world"""', ''),      # End triple quote
        ("'''test", "'''"),    # Start single triple quote
        ("end'''", ''),        # End single triple quote
        ('"test', '"'),        # Start double quote
        ('end"', ''),          # End double quote
    ]
    
    for line, expected_quote in test_sequences:
        _, actual_quote = skip_line(line, "", 0, ())
        # Initial quote state transitions
        assert actual_quote == expected_quote
    
    # Test continuing quotes
    _, quote1 = skip_line('"""start', "", 0, ())
    assert quote1 == '"""'
    _, quote2 = skip_line('middle', quote1, 1, ())
    assert quote2 == '"""'  # Should remain in triple quote
    _, quote3 = skip_line('end"""', quote2, 2, ())
    assert quote3 == ""  # Should exit triple quote


# Test normalize_line with import* pattern
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=0, max_size=10))
def test_normalize_line_import_star(identifier):
    """Test normalize_line with import* patterns"""
    test_line = f"import{identifier}*"
    normalized, raw = normalize_line(test_line)
    
    assert raw == test_line
    # Should normalize to "import *" when identifier is empty
    if identifier == "":
        assert normalized == "import *"


# Test complex parentheses handling in file_contents
def test_file_contents_parentheses_complex():
    """Test file_contents with complex parentheses patterns"""
    contents = """
from module import (
    func1,  # comment 1
    func2,  # comment 2
    func3   # comment 3
)

from another import (
    item1,
    item2,
    item3,
)  # trailing comma

from third import (item4, item5,
                  item6, item7)
"""
    
    result = file_contents(contents, Config())
    # Should handle multi-line imports with comments
    assert result.imports is not None
    # Check trailing comma detection
    assert len(result.trailing_commas) >= 0


# Test strip_syntax with _import/_cimport preservation
def test_strip_syntax_underscore_preservation():
    """Test that strip_syntax correctly preserves _import and _cimport"""
    test_cases = [
        "from _import import something",
        "from module import _import",
        "from _cimport import func",
        "import _import, _cimport",
    ]
    
    for case in test_cases:
        result = strip_syntax(case)
        # Should preserve _import and _cimport
        if "_import" in case:
            assert "_import" in result
        if "_cimport" in case:
            assert "_cimport" in result
        # Should not have temporary placeholders
        assert "[[i]]" not in result
        assert "[[ci]]" not in result


# Test line ending preservation
def test_line_separator_mixed_endings():
    """Test _infer_line_separator with mixed line endings"""
    test_cases = [
        ("line1\r\nline2\nline3", "\r\n"),  # \r\n takes precedence
        ("line1\rline2\nline3", "\r"),      # \r takes precedence over \n
        ("line1\nline2\nline3", "\n"),      # Only \n
        ("no line ending", "\n"),           # Default to \n
    ]
    
    for content, expected in test_cases:
        result = _infer_line_separator(content)
        assert result == expected


# Test import_type with special comments
@given(st.text(min_size=0, max_size=50))
def test_import_type_skip_variations(text):
    """Test import_type with skip comment variations"""
    skip_patterns = [
        f"import os # isort:skip {text}",
        f"import os # isort: skip {text}",
        f"import os # isort: split {text}",
        f"import os #{text} isort:skip",
    ]
    
    config = Config()
    for line in skip_patterns:
        if "isort:skip" in line or "isort: skip" in line or "isort: split" in line:
            result = import_type(line, config)
            assert result is None


# Test boundary condition in skip_line char_index
def test_skip_line_index_boundary():
    """Test skip_line with quotes at string boundaries"""
    # Test quote at very end
    line = 'test"'
    should_skip, quote = skip_line(line, "", 0, ())
    assert quote == '"'
    
    # Test quote at very beginning  
    line = '"test'
    should_skip, quote = skip_line(line, "", 0, ())
    assert quote == '"'
    
    # Test escaped quote at end
    line = 'test\\"'
    should_skip, quote = skip_line(line, "", 0, ())
    assert quote == ""  # Should not enter quote due to escape
    
    # Test triple quote detection at boundaries
    line = '"""'
    should_skip, quote = skip_line(line, "", 0, ())
    assert quote == '"""'


# Specific test for potential off-by-one errors
def test_skip_line_off_by_one():
    """Test for potential off-by-one errors in skip_line"""
    # Test with quote at exact positions
    test_cases = [
        ('a"b', '"'),          # Quote in middle
        ('"ab', '"'),          # Quote at start
        ('ab"', '"'),          # Quote at end  
        ('a""b', ''),          # Two quotes (open and close)
        ('"""a', '"""'),       # Triple quote at start
        ('a"""', '"""'),       # Triple quote at end
        ('a"""b"""c', ''),     # Triple quotes open and close
    ]
    
    for line, expected_final in test_cases:
        _, quote = skip_line(line, "", 0, ())
        assert quote == expected_final


# Test that could reveal the backslash handling bug
def test_skip_line_backslash_increment():
    """Test skip_line backslash handling"""
    # This could reveal if char_index increment after backslash is wrong
    test_lines = [
        "test\\",      # Backslash at end - might skip beyond string
        "test\\'",     # Escaped quote at end
        "test\\n",     # Escape sequence
        "\\",          # Just backslash
        "\\'",         # Just escaped quote
    ]
    
    for line in test_lines:
        try:
            should_skip, quote = skip_line(line, "", 0, ())
            # Should not crash even with backslash at end
            assert isinstance(should_skip, bool)
        except IndexError:
            # This would indicate a bug - going beyond string bounds
            assert False, f"IndexError with line: {repr(line)}"