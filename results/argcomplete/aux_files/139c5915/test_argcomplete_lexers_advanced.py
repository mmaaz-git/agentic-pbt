import os
import string
from hypothesis import given, strategies as st, assume, settings, example
import argcomplete.lexers


@given(st.text(alphabet='"`\'\\', min_size=1, max_size=50))
def test_quote_and_escape_combinations(text):
    """Test complex quote and escape character combinations"""
    try:
        result = argcomplete.lexers.split_line(text)
        assert isinstance(result, tuple)
        assert len(result) == 5
        # Function should handle any quote/escape combination without crashing
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(
    st.text(alphabet=string.printable, min_size=1, max_size=100),
    st.integers(min_value=0)
)
def test_point_in_quoted_string(line, point):
    """Test point parameter when it falls inside quoted strings"""
    # Add quotes to the line
    quoted_line = f'echo "{line}"'
    point = min(point, len(quoted_line))
    
    try:
        result = argcomplete.lexers.split_line(quoted_line, point)
        prequote, prefix, suffix, words, wordbreak = result
        
        # If point is inside the quoted part, prequote might be set
        if 6 <= point < len(quoted_line) - 1:  # Inside the quotes
            # We're inside a quoted string
            pass  # Just ensure no crash
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(st.text(min_size=1000, max_size=10000))
@settings(max_examples=10)
def test_very_long_input(long_text):
    """Test with very long input strings"""
    try:
        result = argcomplete.lexers.split_line(long_text)
        assert isinstance(result, tuple)
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(st.text(alphabet='|&;<>()$`\\', min_size=1, max_size=50))
def test_shell_metacharacters(text):
    """Test with shell metacharacters"""
    try:
        result = argcomplete.lexers.split_line(text)
        assert isinstance(result, tuple)
        assert len(result) == 5
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(st.text())
def test_with_env_wordbreaks(line):
    """Test with custom COMP_WORDBREAKS environment variable"""
    original = os.environ.get("_ARGCOMPLETE_COMP_WORDBREAKS")
    
    try:
        # Set various wordbreak characters
        os.environ["_ARGCOMPLETE_COMP_WORDBREAKS"] = "\"'><=;|&(:"
        result1 = argcomplete.lexers.split_line(line)
        
        # Different wordbreaks should potentially give different results
        os.environ["_ARGCOMPLETE_COMP_WORDBREAKS"] = " "
        result2 = argcomplete.lexers.split_line(line)
        
        # Both should still be valid tuples
        assert isinstance(result1, tuple) and len(result1) == 5
        assert isinstance(result2, tuple) and len(result2) == 5
        
    except argcomplete.lexers.ArgcompleteException:
        pass
    finally:
        # Restore original value
        if original is not None:
            os.environ["_ARGCOMPLETE_COMP_WORDBREAKS"] = original
        else:
            os.environ.pop("_ARGCOMPLETE_COMP_WORDBREAKS", None)


@given(st.text(alphabet=string.printable.replace('"', '').replace("'", ''), min_size=1, max_size=50))
def test_mixed_quotes(content):
    """Test mixing single and double quotes"""
    # Create strings with mixed quotes
    mixed1 = f'echo "{content}" \'{content}\''
    mixed2 = f"echo '{content}' \"{content}\""
    
    try:
        result1 = argcomplete.lexers.split_line(mixed1)
        result2 = argcomplete.lexers.split_line(mixed2)
        
        # Both should parse successfully
        assert isinstance(result1, tuple) and len(result1) == 5
        assert isinstance(result2, tuple) and len(result2) == 5
        
        # Both should identify 'echo' as the first word
        assert result1[3][0] == 'echo' if result1[3] else True
        assert result2[3][0] == 'echo' if result2[3] else True
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(st.integers(min_value=-1000000, max_value=1000000))
def test_point_extreme_values(point):
    """Test with extreme point values"""
    line = "ls -la /tmp"
    
    try:
        result = argcomplete.lexers.split_line(line, point)
        assert isinstance(result, tuple)
        assert len(result) == 5
    except (ValueError, IndexError, argcomplete.lexers.ArgcompleteException, AssertionError):
        # Any of these exceptions are acceptable for extreme values
        pass


@given(st.text(alphabet='\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r', min_size=1, max_size=20))
def test_control_characters(text):
    """Test with control characters"""
    try:
        result = argcomplete.lexers.split_line(text)
        assert isinstance(result, tuple)
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(st.text())
@example('')  # Empty string
@example(' ')  # Single space
@example('  ')  # Multiple spaces
@example('\t')  # Tab
@example('\n')  # Newline
def test_whitespace_edge_cases(text):
    """Test various whitespace edge cases"""
    try:
        result = argcomplete.lexers.split_line(text)
        prequote, prefix, suffix, words, wordbreak = result
        
        # For pure whitespace, we expect empty results
        if text.strip() == '':
            assert prefix == ''
            assert suffix == ''
            assert words == []
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(st.text(min_size=1, max_size=100))
def test_unclosed_quotes_with_point(line):
    """Test unclosed quotes with various point positions"""
    # Add an unclosed quote
    quoted_line = line + '"'
    
    for point in [0, len(quoted_line)//2, len(quoted_line)]:
        try:
            result = argcomplete.lexers.split_line(quoted_line, point)
            prequote, prefix, suffix, words, wordbreak = result
            # Unclosed quote might be indicated in prequote
            assert isinstance(prequote, str)
        except argcomplete.lexers.ArgcompleteException:
            pass


@given(
    st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10), min_size=2, max_size=5),
    st.integers(min_value=0, max_value=100)
)
def test_word_boundary_detection(words_list, extra_spaces):
    """Test that word boundaries are correctly detected"""
    # Join words with varying amounts of whitespace
    spaces = ' ' * (1 + extra_spaces % 5)
    line = spaces.join(words_list)
    
    result = argcomplete.lexers.split_line(line)
    prequote, prefix, suffix, words, wordbreak = result
    
    # Number of detected words should match input (excluding current word in prefix)
    total_words = len(words) + (1 if prefix else 0)
    assert total_words == len(words_list)