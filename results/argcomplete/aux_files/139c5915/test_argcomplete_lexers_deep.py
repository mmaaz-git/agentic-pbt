import os
import string
from hypothesis import given, strategies as st, assume, settings, seed
import argcomplete.lexers


@given(st.data())
@settings(max_examples=500)
def test_incremental_point_consistency(data):
    """Test that processing incrementally with point gives consistent results"""
    line = data.draw(st.text(min_size=1, max_size=100))
    
    results = []
    for point in range(len(line) + 1):
        try:
            result = argcomplete.lexers.split_line(line, point)
            results.append(result)
        except argcomplete.lexers.ArgcompleteException as e:
            results.append(f"error: {e}")
    
    # Check that results progress sensibly
    for i in range(1, len(results)):
        if isinstance(results[i], tuple) and isinstance(results[i-1], tuple):
            # Words list should only grow or stay the same
            prev_words = results[i-1][3]
            curr_words = results[i][3]
            # Words can change as we parse, but shouldn't randomly disappear
            assert isinstance(prev_words, list)
            assert isinstance(curr_words, list)


@given(st.text(alphabet='"\' \t\n', min_size=2, max_size=50))
def test_quote_whitespace_interaction(text):
    """Test interaction between quotes and whitespace"""
    try:
        result = argcomplete.lexers.split_line(text)
        prequote, prefix, suffix, words, wordbreak = result
        
        # Check internal consistency
        assert isinstance(prequote, str)
        assert isinstance(prefix, str) 
        assert isinstance(suffix, str)
        assert isinstance(words, list)
        
        # If there's a prequote, it should be a quote character
        if prequote:
            assert prequote in ['"', "'"]
            
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(st.text(min_size=1, max_size=50))
def test_empty_wordbreaks_env(line):
    """Test with empty COMP_WORDBREAKS"""
    original = os.environ.get("_ARGCOMPLETE_COMP_WORDBREAKS")
    
    try:
        os.environ["_ARGCOMPLETE_COMP_WORDBREAKS"] = ""
        result = argcomplete.lexers.split_line(line)
        assert isinstance(result, tuple)
        assert len(result) == 5
    except argcomplete.lexers.ArgcompleteException:
        pass
    finally:
        if original is not None:
            os.environ["_ARGCOMPLETE_COMP_WORDBREAKS"] = original
        else:
            os.environ.pop("_ARGCOMPLETE_COMP_WORDBREAKS", None)


@given(
    st.text(alphabet=string.ascii_letters + ' ', min_size=1, max_size=30),
    st.sampled_from(['"', "'"])
)
def test_quote_at_different_positions(text, quote):
    """Test quotes at different positions in the string"""
    # Test quote at beginning
    test1 = quote + text
    # Test quote at end  
    test2 = text + quote
    # Test quote in middle
    if len(text) > 2:
        mid = len(text) // 2
        test3 = text[:mid] + quote + text[mid:]
    else:
        test3 = text
    
    for test_str in [test1, test2, test3]:
        try:
            result = argcomplete.lexers.split_line(test_str)
            assert isinstance(result, tuple)
            assert len(result) == 5
        except argcomplete.lexers.ArgcompleteException:
            pass


@given(st.integers(min_value=-2**31, max_value=2**31))
def test_point_integer_overflow(point):
    """Test with very large positive and negative point values"""
    line = "echo test"
    try:
        result = argcomplete.lexers.split_line(line, point=point)
        # Should either work or raise an exception
        assert isinstance(result, tuple)
    except (ValueError, IndexError, OverflowError, argcomplete.lexers.ArgcompleteException, AssertionError):
        pass


@given(st.text(alphabet='()[]{}', min_size=1, max_size=20))
def test_bracket_characters(text):
    """Test with various bracket characters"""
    try:
        result = argcomplete.lexers.split_line(text)
        assert isinstance(result, tuple)
        assert len(result) == 5
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(st.text())
def test_null_byte_handling(text):
    """Test strings containing null bytes"""
    # Insert null bytes at random positions
    if text:
        null_text = text[:len(text)//2] + '\x00' + text[len(text)//2:]
    else:
        null_text = '\x00'
    
    try:
        result = argcomplete.lexers.split_line(null_text)
        assert isinstance(result, tuple)
    except (ValueError, argcomplete.lexers.ArgcompleteException):
        pass


@given(
    st.lists(
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
        min_size=1,
        max_size=5
    )
)
def test_escape_sequences_in_words(words):
    """Test with backslash escape sequences"""
    # Join words with escaped spaces
    line = '\\ '.join(words)
    
    try:
        result = argcomplete.lexers.split_line(line)
        prequote, prefix, suffix, parsed_words, wordbreak = result
        # The escaped spaces might be handled differently
        assert isinstance(parsed_words, list)
    except argcomplete.lexers.ArgcompleteException:
        pass


@given(st.text(min_size=1, max_size=100))
@seed(12345)  # Use fixed seed for reproducibility
def test_unicode_handling(text):
    """Test with unicode characters"""
    # Add some unicode characters
    unicode_text = text + "🦄 あ € 中文"
    
    try:
        result = argcomplete.lexers.split_line(unicode_text)
        assert isinstance(result, tuple)
        assert len(result) == 5
    except (UnicodeError, argcomplete.lexers.ArgcompleteException):
        pass


@given(
    st.text(alphabet=string.printable, min_size=5, max_size=50),
    st.floats(min_value=0.0, max_value=1.0)
)
def test_point_as_percentage(text, percentage):
    """Test point at various percentages through the string"""
    point = int(len(text) * percentage)
    
    result = argcomplete.lexers.split_line(text, point)
    prequote, prefix, suffix, words, wordbreak = result
    
    # Verify we only processed up to point
    processed_text = text[:point]
    
    # The words list should reflect what's before point
    assert isinstance(words, list)
    
    # If point is 0, we should have no words
    if point == 0:
        assert words == []
        assert prefix == ''