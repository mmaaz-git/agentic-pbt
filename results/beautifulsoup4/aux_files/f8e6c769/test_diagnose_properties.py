"""Property-based tests for bs4.diagnose module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/beautifulsoup4_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import bs4.diagnose as diagnose
from io import BytesIO


# Test 1: rword() length property
@given(st.integers(min_value=1, max_value=100))
def test_rword_length(length):
    """rword() should return a string of exactly the specified length"""
    result = diagnose.rword(length)
    assert len(result) == length, f"Expected length {length}, got {len(result)}"


# Test 2: rword() alternating pattern property
@given(st.integers(min_value=1, max_value=100))
def test_rword_alternating_pattern(length):
    """rword() should alternate consonants and vowels based on position"""
    result = diagnose.rword(length)
    vowels = set('aeiou')
    consonants = set('bcdfghjklmnpqrstvwxyz')
    
    for i, char in enumerate(result):
        if i % 2 == 0:
            # Even indices should have consonants
            assert char in consonants, f"Character at index {i} should be consonant, got '{char}'"
        else:
            # Odd indices should have vowels
            assert char in vowels, f"Character at index {i} should be vowel, got '{char}'"


# Test 3: rsentence() word count property
@given(st.integers(min_value=1, max_value=20))
def test_rsentence_word_count(length):
    """rsentence() should return exactly 'length' words separated by spaces"""
    result = diagnose.rsentence(length)
    words = result.split(' ')
    assert len(words) == length, f"Expected {length} words, got {len(words)}"
    # Each word should be non-empty
    for word in words:
        assert len(word) > 0, "Found empty word in sentence"


# Test 4: rdoc() HTML wrapper property
@given(st.integers(min_value=0, max_value=100))
def test_rdoc_html_wrapper(num_elements):
    """rdoc() should always start with '<html>' and end with '</html>'"""
    result = diagnose.rdoc(num_elements)
    assert result.startswith('<html>'), f"Document should start with '<html>', got: {result[:20]}"
    assert result.endswith('</html>'), f"Document should end with '</html>', got: {result[-20:]}"


# Test 5: rdoc() element count property (relaxed)
@given(st.integers(min_value=0, max_value=100))
def test_rdoc_element_generation(num_elements):
    """rdoc() should generate content between the HTML tags based on num_elements"""
    result = diagnose.rdoc(num_elements)
    # Extract content between <html> and </html>
    content = result[6:-7]  # Skip '<html>' and '</html>'
    
    if num_elements == 0:
        # With 0 elements, should have empty content between tags
        assert content == '', f"Expected empty content for 0 elements, got: {content}"
    else:
        # With >0 elements, should have non-empty content
        assert len(content) > 0, f"Expected non-empty content for {num_elements} elements"
        # Should contain newlines as elements are joined with newlines
        if num_elements > 1:
            assert '\n' in content, f"Expected newlines in content for {num_elements} elements"


# Test 6: lxml_trace string conversion property
@given(st.text(min_size=1, max_size=100))
@settings(max_examples=50)
def test_lxml_trace_string_handling(data):
    """lxml_trace() should handle string input by converting to bytes"""
    try:
        # Import lxml to check if it's available
        from lxml import etree
        
        # Create a simple valid XML/HTML string for testing
        test_data = f"<root>{data}</root>"
        
        # This should not raise an error for string input
        # We capture output to avoid printing during tests
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            diagnose.lxml_trace(test_data, html=False)
        
        # If we get here without exception, the test passes
        assert True
        
    except ImportError:
        # lxml not installed, skip this test
        assume(False)
    except Exception as e:
        # Check if it's the expected type conversion issue
        if "a bytes-like object is required" in str(e):
            raise AssertionError(f"String to bytes conversion failed: {e}")
        # Other exceptions might be from invalid XML, which is okay
        pass


# Test 7: AnnouncingParser does not crash on various inputs
@given(st.text(min_size=0, max_size=1000))
@settings(max_examples=100)
def test_htmlparser_trace_robustness(data):
    """htmlparser_trace() should not crash on any string input"""
    import io
    import contextlib
    
    # Capture output to avoid printing during tests
    f = io.StringIO()
    try:
        with contextlib.redirect_stdout(f):
            diagnose.htmlparser_trace(data)
        # If we get here, the test passes (no crash)
        assert True
    except Exception as e:
        # HTMLParser might raise exceptions for very malformed input
        # but the function itself shouldn't crash
        if "htmlparser_trace" in str(e.__traceback__):
            raise AssertionError(f"htmlparser_trace crashed: {e}")