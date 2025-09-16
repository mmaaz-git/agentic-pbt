import os
import re
import string
from hypothesis import given, strategies as st, assume, settings, seed, example
import argcomplete.lexers


@given(st.text(alphabet='"\'\\', min_size=1, max_size=100))
@example('"\\"')  # Escaped quote inside quotes
@example("'\\''")  # Escaped quote inside single quotes  
@example('"\\\n"')  # Escaped newline in quotes
@example('"\\')  # Unclosed quote with trailing backslash
@example('\\')  # Just a backslash
@example('\\\\')  # Double backslash
@example('"\\\\')  # Double backslash in unclosed quote
def test_complex_escape_sequences(text):
    """Test complex escape sequences that might trigger edge cases"""
    try:
        result = argcomplete.lexers.split_line(text)
        assert isinstance(result, tuple)
        assert len(result) == 5
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(st.data())
def test_point_at_quote_boundaries(data):
    """Test point parameter at exact quote boundaries"""
    content = data.draw(st.text(alphabet=string.ascii_letters, min_size=1, max_size=20))
    quote = data.draw(st.sampled_from(['"', "'"]))
    
    # Build string with quotes
    test_string = f'echo {quote}{content}{quote}'
    
    # Test at critical points
    critical_points = [
        5,  # Just before the opening quote
        6,  # At the opening quote
        7,  # Just after the opening quote
        len(test_string) - 1,  # At the closing quote
        len(test_string),  # Just after the closing quote
    ]
    
    for point in critical_points:
        if point <= len(test_string):
            try:
                result = argcomplete.lexers.split_line(test_string, point)
                assert isinstance(result, tuple)
            except argcomplete.lexers.ArgcompleteException:
                pass


@given(st.text(min_size=1, max_size=50))
def test_wordbreaks_with_special_chars(text):
    """Test with wordbreaks containing special regex characters"""
    original = os.environ.get("_ARGCOMPLETE_COMP_WORDBREAKS")
    
    # Use regex special characters as wordbreaks
    special_wordbreaks = ".*+?[]{}()|^$\\"
    
    try:
        os.environ["_ARGCOMPLETE_COMP_WORDBREAKS"] = special_wordbreaks
        result = argcomplete.lexers.split_line(text)
        assert isinstance(result, tuple)
    except (argcomplete.lexers.ArgcompleteException, ValueError, re.error):
        pass
    finally:
        if original is not None:
            os.environ["_ARGCOMPLETE_COMP_WORDBREAKS"] = original
        else:
            os.environ.pop("_ARGCOMPLETE_COMP_WORDBREAKS", None)


@given(
    st.text(alphabet=string.ascii_letters + ' ', min_size=10, max_size=50),
    st.integers(min_value=1, max_value=10)
)
def test_multiple_unclosed_quotes(text, num_quotes):
    """Test with multiple unclosed quotes"""
    # Add multiple unclosed quotes at random positions
    for _ in range(num_quotes):
        pos = len(text) // (num_quotes + 1)
        text = text[:pos] + '"' + text[pos:]
    
    try:
        result = argcomplete.lexers.split_line(text)
        prequote, prefix, suffix, words, wordbreak = result
        # With unclosed quotes, prequote might be set
        assert isinstance(result, tuple)
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(st.lists(st.sampled_from(['|', '&&', '||', ';', '&']), min_size=1, max_size=5))
def test_shell_operators_sequence(operators):
    """Test sequences of shell operators"""
    # Create a command with multiple operators
    parts = ['echo', 'test']
    for op in operators:
        parts.append(op)
        parts.append('echo')
        parts.append('test')
    
    line = ' '.join(parts)
    
    try:
        result = argcomplete.lexers.split_line(line)
        prequote, prefix, suffix, words, wordbreak = result
        
        # Operators should be parsed as separate words
        assert isinstance(words, list)
        # Check that operators are in the words list
        for op in operators[:-1]:  # Last one might be in current word
            assert op in words or op == prefix
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(st.text())
@example('echo "$(ls)"')  # Command substitution in quotes
@example('echo `ls`')  # Backticks
@example('echo ${VAR}')  # Variable expansion
@example('echo $((2+2))')  # Arithmetic expansion
@example('echo ~user')  # Tilde expansion
@example('echo file{1,2,3}')  # Brace expansion
def test_bash_expansions(text):
    """Test various bash expansion syntaxes"""
    try:
        result = argcomplete.lexers.split_line(text)
        assert isinstance(result, tuple)
        assert len(result) == 5
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(
    st.text(alphabet=string.printable, min_size=5, max_size=50),
    st.integers(min_value=0, max_value=10)
)
def test_repeated_parsing_with_different_points(text, offset):
    """Test parsing the same string with slightly different points"""
    base_point = len(text) // 2
    
    results = []
    for delta in range(-offset, offset + 1):
        point = base_point + delta
        if 0 <= point <= len(text):
            try:
                result = argcomplete.lexers.split_line(text, point)
                results.append((point, result))
            except argcomplete.lexers.ArgcompleteException as e:
                results.append((point, str(e)))
    
    # Results should change predictably as point increases
    for i in range(1, len(results)):
        if isinstance(results[i][1], tuple) and isinstance(results[i-1][1], tuple):
            curr_point = results[i][0]
            prev_point = results[i-1][0]
            
            if curr_point > prev_point:
                # As point increases, we process more of the string
                curr_words = results[i][1][3]
                prev_words = results[i-1][1][3]
                
                # Word count should not decrease (might stay same or increase)
                assert len(curr_words) >= len(prev_words) - 1  # -1 for edge cases


# Looking for the "Unexpected internal state" error
@given(st.text(min_size=2, max_size=100))
def test_trigger_internal_state_error(text):
    """Try to trigger the 'Unexpected internal state' error"""
    # This error occurs when lexer.instream.tell() < point after a ValueError
    # Try to create conditions that might trigger this
    
    # Add some quotes and special characters that might cause ValueError
    problem_text = '"' + text + '\\'  # Unclosed quote with trailing backslash
    
    # Try various points
    for point in [len(problem_text) // 2, len(problem_text) - 1]:
        try:
            result = argcomplete.lexers.split_line(problem_text, point)
            assert isinstance(result, tuple)
        except argcomplete.lexers.ArgcompleteException as e:
            # Check if we triggered the internal state error
            if "Unexpected internal state" in str(e):
                # This would be interesting but not necessarily a bug
                pass


@given(st.text(alphabet=' \t\n\r\f\v', min_size=1, max_size=50))
def test_only_whitespace_with_point(whitespace):
    """Test strings containing only various whitespace characters with different points"""
    for point in [0, len(whitespace) // 2, len(whitespace)]:
        result = argcomplete.lexers.split_line(whitespace, point)
        prequote, prefix, suffix, words, wordbreak = result
        
        # For pure whitespace, should have empty results
        assert prefix == ''
        assert suffix == ''
        assert words == []
        assert prequote == ''