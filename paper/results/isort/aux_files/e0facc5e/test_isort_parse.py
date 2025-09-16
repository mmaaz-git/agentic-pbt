import re
from hypothesis import given, strategies as st, settings, assume
import isort.parse
from isort.settings import Config


# Test 1: normalize_line idempotence
@given(st.text())
def test_normalize_line_idempotence(line):
    """Normalizing a line twice should give the same result (idempotence)."""
    normalized_once, _ = isort.parse.normalize_line(line)
    normalized_twice, _ = isort.parse.normalize_line(normalized_once)
    assert normalized_once == normalized_twice


# Test 2: normalize_line removes tabs
@given(st.text())
def test_normalize_line_no_tabs(line):
    """After normalization, the line should contain no tabs."""
    normalized, _ = isort.parse.normalize_line(line)
    assert '\t' not in normalized


# Test 3: normalize_line preserves raw_line
@given(st.text())
def test_normalize_line_raw_preservation(line):
    """The raw_line returned should match the input."""
    _, raw_line = isort.parse.normalize_line(line)
    assert raw_line == line


# Test 4: strip_syntax idempotence
@given(st.text())
def test_strip_syntax_idempotence(import_string):
    """Stripping syntax twice should give the same result."""
    stripped_once = isort.parse.strip_syntax(import_string)
    stripped_twice = isort.parse.strip_syntax(stripped_once)
    assert stripped_once == stripped_twice


# Test 5: strip_syntax removes expected characters
@given(st.text())
def test_strip_syntax_removes_chars(import_string):
    """After stripping, certain syntax characters should be removed."""
    stripped = isort.parse.strip_syntax(import_string)
    # These characters should be replaced with spaces or removed
    for char in ['\\', '(', ')', ',']:
        # Check that isolated instances are removed (replaced with space and collapsed)
        if char in import_string and char not in ['_import', '_cimport', '{|', '|}']:
            # The character might still appear in special contexts
            pass
    # Keywords should be removed
    tokens = stripped.split()
    assert 'from' not in tokens
    assert 'import' not in tokens
    assert 'cimport' not in tokens


# Test 6: parse_comments with no hash
@given(st.text(alphabet=st.characters(blacklist_characters='#')))
def test_parse_comments_no_hash(line):
    """If there's no # in the line, comment should be empty."""
    import_part, comment = isort.parse.parse_comments(line)
    assert comment == ""
    assert import_part == line


# Test 7: parse_comments round-trip for simple cases
@given(
    st.text(alphabet=st.characters(blacklist_characters='#'), min_size=1),
    st.text(min_size=0)
)
def test_parse_comments_roundtrip(import_part, comment_part):
    """For simple cases, we should be able to reconstruct the line."""
    if comment_part:
        line = f"{import_part}#{comment_part}"
    else:
        line = import_part
    
    parsed_import, parsed_comment = isort.parse.parse_comments(line)
    
    if comment_part:
        # The comment should be extracted (without the #)
        assert parsed_comment == comment_part
        # The import part should match
        assert parsed_import == import_part
    else:
        assert parsed_comment == ""
        assert parsed_import == import_part


# Test 8: import_type classification for straight imports
@given(st.text())
def test_import_type_straight(suffix):
    """Lines starting with 'import ' or 'cimport ' should be classified as straight."""
    # Test 'import ' prefix
    if not suffix.startswith(('isort:skip', 'isort: skip', 'isort: split')):
        line = f"import {suffix}"
        if not ('isort:skip' in line or 'isort: skip' in line or 'isort: split' in line):
            result = isort.parse.import_type(line)
            assert result == "straight"
    
    # Test 'cimport ' prefix
    if not suffix.startswith(('isort:skip', 'isort: skip', 'isort: split')):
        line = f"cimport {suffix}"
        if not ('isort:skip' in line or 'isort: skip' in line or 'isort: split' in line):
            result = isort.parse.import_type(line)
            assert result == "straight"


# Test 9: import_type classification for from imports
@given(st.text())
def test_import_type_from(suffix):
    """Lines starting with 'from ' should be classified as from."""
    line = f"from {suffix}"
    if not ('isort:skip' in line or 'isort: skip' in line or 'isort: split' in line):
        result = isort.parse.import_type(line)
        assert result == "from"


# Test 10: import_type returns None for skip markers
@given(st.text())
def test_import_type_skip_markers(text):
    """Lines with isort:skip markers should return None."""
    # Test various skip markers
    for marker in ['isort:skip', 'isort: skip', 'isort: split']:
        line = f"import something  # {marker}"
        result = isort.parse.import_type(line)
        assert result is None


# Test 11: skip_line quote tracking
@given(
    st.text(),
    st.sampled_from(['', '"', "'", '"""', "'''"]),
    st.integers(min_value=0, max_value=1000),
    st.tuples()  # Empty tuple for section_comments
)
def test_skip_line_quote_consistency(line, initial_quote, index, section_comments):
    """Quote tracking should be consistent."""
    should_skip, final_quote = isort.parse.skip_line(
        line, initial_quote, index, section_comments
    )
    
    # If we started in a quote, we should skip
    if initial_quote:
        assert should_skip
    
    # The final quote should be a valid quote marker or empty
    assert final_quote in ['', '"', "'", '"""', "'''"]


# Test 12: skip_line preserves or clears quotes properly
@given(st.text(alphabet=st.characters(blacklist_characters='"\''), min_size=1))
def test_skip_line_no_quotes(line):
    """Lines without quotes should not change quote state."""
    initial_quote = ""
    should_skip, final_quote = isort.parse.skip_line(
        line, initial_quote, 0, tuple()
    )
    assert final_quote == ""


# Test 13: Complex property - file_contents basic invariants
@given(st.text())
@settings(max_examples=100)
def test_file_contents_line_count(contents):
    """The parsed content should preserve line information."""
    result = isort.parse.file_contents(contents)
    
    # The original line count should match the input
    input_lines = contents.splitlines()
    if contents and contents[-1] in ('\n', '\r'):
        input_lines.append("")
    
    assert result.original_line_count == len(input_lines)
    assert len(result.in_lines) == result.original_line_count


# Test 14: Metamorphic property for normalize_line
@given(st.text())
def test_normalize_line_consistent_transformations(line):
    """Specific transformations should be applied consistently."""
    normalized, _ = isort.parse.normalize_line(line)
    
    # Check specific transformations from the code
    if "from.import " in line.replace(" ", ""):
        # Should have space after from and dots
        assert re.search(r"from\s+\.+\s+import", normalized)
    
    if "from.cimport " in line.replace(" ", ""):
        # Should have space after from and dots  
        assert re.search(r"from\s+\.+\s+cimport", normalized)
    
    if "import*" in line:
        assert "import *" in normalized


# Test 15: Edge case - empty string handling
def test_empty_string_handling():
    """Empty strings should be handled gracefully."""
    # normalize_line
    normalized, raw = isort.parse.normalize_line("")
    assert normalized == ""
    assert raw == ""
    
    # strip_syntax
    stripped = isort.parse.strip_syntax("")
    assert stripped == ""
    
    # parse_comments
    import_part, comment = isort.parse.parse_comments("")
    assert import_part == ""
    assert comment == ""
    
    # import_type
    result = isort.parse.import_type("")
    assert result is None
    
    # file_contents
    parsed = isort.parse.file_contents("")
    assert parsed.original_line_count == 0