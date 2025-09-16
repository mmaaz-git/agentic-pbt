import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import isort.comments as comments


@given(st.text())
def test_parse_round_trip_property(line):
    """
    If we parse a line and reconstruct it, we should get the original line back.
    """
    import_part, comment_part = comments.parse(line)
    
    if comment_part:
        reconstructed = f"{import_part}# {comment_part}"
        assert reconstructed == line or reconstructed == line.rstrip()
    else:
        assert import_part == line


@given(st.text())
def test_parse_invariant(line):
    """
    The parsed parts should be substrings of the original line.
    """
    import_part, comment_part = comments.parse(line)
    
    # The import part should be a prefix (possibly with trailing whitespace removed)
    assert line.startswith(import_part) or line.startswith(import_part.rstrip())
    
    # If there's a comment, it should appear after a '#' in the original
    if comment_part:
        assert '#' in line
        # The comment (without leading/trailing spaces) should be in the original
        assert comment_part in line


@given(st.text())
def test_parse_idempotence(line):
    """
    Parsing the import part of a parsed line should yield the same import part.
    """
    import_part1, comment_part1 = comments.parse(line)
    import_part2, comment_part2 = comments.parse(import_part1)
    
    assert import_part2 == import_part1
    assert comment_part2 == ""  # After parsing once, the import part has no comment


@given(st.text())
def test_parse_comment_extraction(line):
    """
    When there's a '#' in the line, the comment should be everything after the first '#'.
    """
    import_part, comment_part = comments.parse(line)
    
    if '#' in line:
        hash_index = line.find('#')
        expected_import = line[:hash_index]
        expected_comment = line[hash_index + 1:].strip()
        
        assert import_part == expected_import
        assert comment_part == expected_comment
    else:
        assert comment_part == ""
        assert import_part == line


@given(
    st.lists(st.text()),
    st.text(),
    st.booleans(),
    st.text()
)
def test_add_to_line_removal_property(comments_list, original_string, removed, comment_prefix):
    """
    When removed=True, the function should return only the non-comment part.
    """
    result = comments.add_to_line(comments_list, original_string, removed, comment_prefix)
    
    if removed:
        # Should return only the import part (without comments)
        import_part, _ = comments.parse(original_string)
        assert result == import_part


@given(
    st.lists(st.text(), min_size=1),
    st.text(),
    st.text()
)
def test_add_to_line_uniqueness_property(comments_list, original_string, comment_prefix):
    """
    Duplicate comments should only appear once in the result.
    """
    assume(not any('#' in c for c in comments_list))  # Avoid '#' in comments themselves
    
    # Create a list with duplicates
    comments_with_dups = comments_list + comments_list
    
    result = comments.add_to_line(comments_with_dups, original_string, False, comment_prefix)
    
    # Count occurrences of each unique comment in the result
    for comment in set(comments_list):
        if comment:  # Only check non-empty comments
            # Each comment should appear exactly once in the result
            count = result.count(comment)
            assert count <= 1, f"Comment '{comment}' appears {count} times"


@given(st.text(), st.text())
def test_add_to_line_no_comments_property(original_string, comment_prefix):
    """
    When comments is None or empty, should return original_string.
    """
    result_none = comments.add_to_line(None, original_string, False, comment_prefix)
    result_empty = comments.add_to_line([], original_string, False, comment_prefix)
    
    assert result_none == original_string
    assert result_empty == original_string


@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=10),
    st.text(),
    st.text()
)
def test_add_to_line_comment_preservation(comments_list, original_string, comment_prefix):
    """
    Multiple calls with the same comments should produce consistent results.
    """
    assume(not any('#' in c for c in comments_list))  # Avoid '#' in comments
    assume(all(c.strip() for c in comments_list))  # Non-empty comments
    
    result1 = comments.add_to_line(comments_list, original_string, False, comment_prefix)
    result2 = comments.add_to_line(comments_list, original_string, False, comment_prefix)
    
    assert result1 == result2


@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=5),
    st.text()
)
def test_add_to_line_format(comments_list, comment_prefix):
    """
    Test that comments are properly formatted with semicolons.
    """
    assume(not any('#' in c or ';' in c for c in comments_list))  # Avoid special chars
    assume(all(c.strip() for c in comments_list))  # Non-empty comments
    
    original = "import os"
    result = comments.add_to_line(comments_list, original, False, comment_prefix)
    
    # Should contain the original import part
    assert result.startswith("import os")
    
    # If there are comments, they should be joined with '; '
    unique_comments = []
    for c in comments_list:
        if c not in unique_comments:
            unique_comments.append(c)
    
    if unique_comments:
        expected_comment_part = f"{comment_prefix} {'; '.join(unique_comments)}"
        assert expected_comment_part in result


@given(st.text())
def test_parse_add_to_line_interaction(line):
    """
    Test the interaction between parse and add_to_line.
    """
    # Parse a line
    import_part, comment_part = comments.parse(line)
    
    # If there was a comment, we should be able to add it back
    if comment_part:
        result = comments.add_to_line([comment_part], import_part, False, "#")
        # The result should contain both the import and the comment
        assert import_part in result
        assert comment_part in result