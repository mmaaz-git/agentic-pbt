import string
from hypothesis import given, strategies as st, assume, settings
import argcomplete.lexers


@given(st.text(min_size=0, max_size=500))
def test_split_line_crash_resistance(line):
    """Test that split_line doesn't crash on any string input"""
    try:
        result = argcomplete.lexers.split_line(line)
        assert isinstance(result, tuple)
        assert len(result) == 5
        prequote, prefix, suffix, words, wordbreak = result
        assert isinstance(prequote, str)
        assert isinstance(prefix, str)
        assert isinstance(suffix, str)
        assert isinstance(words, list)
        for word in words:
            assert isinstance(word, str)
    except argcomplete.lexers.ArgcompleteException:
        pass  # Expected exception is fine


@given(st.text(min_size=0, max_size=200))
def test_split_line_idempotence(line):
    """Test that parsing the same string multiple times gives the same result"""
    result1 = argcomplete.lexers.split_line(line)
    result2 = argcomplete.lexers.split_line(line)
    assert result1 == result2


@given(
    st.text(min_size=0, max_size=200),
    st.integers(min_value=0)
)
def test_split_line_point_boundary(line, point):
    """Test that point parameter is handled correctly"""
    # Only test valid point values
    assume(point <= len(line))
    
    result = argcomplete.lexers.split_line(line, point)
    assert isinstance(result, tuple)
    assert len(result) == 5
    
    # The function should only process up to point
    prequote, prefix, suffix, words, wordbreak = result
    
    # Verify that we're only looking at the first 'point' characters
    truncated_line = line[:point]
    result_truncated = argcomplete.lexers.split_line(truncated_line)
    
    # The results should be similar (though suffix might differ)
    assert result[0] == result_truncated[0]  # prequote
    assert result[3] == result_truncated[3]  # words list


@given(st.text(min_size=0, max_size=200))
def test_split_line_point_none_vs_len(line):
    """Test that point=None is equivalent to point=len(line)"""
    result_none = argcomplete.lexers.split_line(line, point=None)
    result_len = argcomplete.lexers.split_line(line, point=len(line))
    assert result_none == result_len


@given(st.text(alphabet=string.ascii_letters + string.digits + " -", min_size=1, max_size=100))
def test_split_line_reconstruction_simple(line):
    """Test reconstruction property for simple alphanumeric input"""
    prequote, prefix, suffix, words, wordbreak = argcomplete.lexers.split_line(line)
    
    # For simple input without quotes, we should be able to roughly reconstruct
    all_parts = words + ([prefix] if prefix else [])
    if suffix:
        # suffix indicates there's more after the cursor
        all_parts.append(suffix)
    
    # The reconstructed command should have the same words
    reconstructed = ' '.join(all_parts)
    original_words = line.strip().split()
    reconstructed_words = reconstructed.split()
    
    # If line ends with space, current word might be empty
    if line and not line[-1].isspace():
        assert len(reconstructed_words) == len(original_words)


@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=0, max_value=100)
)
def test_split_line_point_out_of_bounds(line, offset):
    """Test that point > len(line) is handled"""
    point = len(line) + offset + 1
    
    # This should either work or raise an appropriate exception
    try:
        result = argcomplete.lexers.split_line(line, point)
        # If it works, the result should be similar to point=len(line)
        result_normal = argcomplete.lexers.split_line(line, len(line))
        # The function might handle this by treating it as len(line)
        assert isinstance(result, tuple)
    except (ValueError, IndexError, argcomplete.lexers.ArgcompleteException):
        # These are acceptable exceptions for out-of-bounds
        pass


@given(st.text(alphabet='"\'', min_size=1, max_size=10))
def test_split_line_quote_only_strings(quote_string):
    """Test strings containing only quote characters"""
    try:
        result = argcomplete.lexers.split_line(quote_string)
        assert isinstance(result, tuple)
        assert len(result) == 5
    except argcomplete.lexers.ArgcompleteException:
        pass  # Expected for malformed quote strings


@given(st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=20), min_size=1, max_size=5))
def test_split_line_word_count_property(words_list):
    """Test that the number of complete words is preserved"""
    line = ' '.join(words_list)
    prequote, prefix, suffix, words, wordbreak = argcomplete.lexers.split_line(line)
    
    # The last word might be in prefix, so total should match
    total_words = len(words) + (1 if prefix else 0)
    assert total_words == len(words_list)


@given(st.text(min_size=0, max_size=200))
@settings(max_examples=500)
def test_split_line_negative_point(line):
    """Test that negative point values are handled"""
    try:
        result = argcomplete.lexers.split_line(line, point=-1)
        # If it works, it might treat negative as 0
        assert isinstance(result, tuple)
    except (ValueError, IndexError, argcomplete.lexers.ArgcompleteException, AssertionError):
        # These are acceptable behaviors for negative point
        pass