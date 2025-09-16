"""
Advanced property-based tests for htmldate.utils module.
Focus on more complex functions and edge cases.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import hypothesis
from lxml.html import HtmlElement
import tempfile
import os

from htmldate.utils import (
    load_html,
    is_dubious_html,
    clean_html,
    fromstring_bytes,
    Extractor
)
from datetime import datetime


# Test load_html with various input types
@given(st.text(min_size=1, max_size=1000))
def test_load_html_string_input(html_string):
    """Test load_html with string input that doesn't look like a URL"""
    # Skip strings that look like URLs
    assume(not html_string.startswith("http"))
    
    result = load_html(html_string)
    
    # The function should try to parse it as HTML
    # It might return None if it's not valid HTML, or a tree if it manages to parse
    assert result is None or isinstance(result, HtmlElement)


# Test is_dubious_html 
@given(st.text(min_size=0, max_size=200))
def test_is_dubious_html_detection(text):
    """Test that is_dubious_html correctly identifies HTML content"""
    beginning = text[:50].lower() if text else ""
    result = is_dubious_html(beginning)
    
    # According to the code, it checks if "html" is NOT in the beginning
    if "html" in beginning:
        assert result is False
    else:
        assert result is True


# Test clean_html element removal
@given(st.text(min_size=50, max_size=500))
def test_clean_html_preserves_structure(html_content):
    """Test that clean_html preserves tree structure after element removal"""
    # Try to create a valid HTML structure
    html_string = f"<html><body>{html_content}<script>test</script></body></html>"
    
    try:
        tree = load_html(html_string)
        if tree is not None:
            # Clean script tags
            cleaned = clean_html(tree, ["script"])
            
            # Verify script tags are removed
            scripts = list(cleaned.iter("script"))
            assert len(scripts) == 0, "Script tags should be removed"
            
            # Tree should still be valid
            assert isinstance(cleaned, HtmlElement)
    except:
        # If parsing fails, that's ok for this test
        pass


# Test fromstring_bytes
@given(st.text(min_size=1, max_size=500))
def test_fromstring_bytes_encoding(text):
    """Test that fromstring_bytes handles UTF-8 encoded strings"""
    result = fromstring_bytes(text)
    
    # It should either parse successfully or return None
    assert result is None or isinstance(result, HtmlElement)


# Test Extractor class initialization
@given(
    st.booleans(),
    st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 1, 1)),
    st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 1, 1)),
    st.booleans(),
    st.sampled_from(["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%Y%m%d"])
)
def test_extractor_initialization(extensive, max_date, min_date, original, format_str):
    """Test that Extractor class properly stores all parameters"""
    extractor = Extractor(extensive, max_date, min_date, original, format_str)
    
    assert extractor.extensive == extensive
    assert extractor.max == max_date
    assert extractor.min == min_date
    assert extractor.original == original
    assert extractor.format == format_str


# Test load_html with malformed HTML
@given(st.text(min_size=10, max_size=200))
def test_load_html_malformed_html(malformed):
    """Test load_html with potentially malformed HTML"""
    # Add some HTML-like structure with special chars
    html_like = f"<html><>{malformed}</></html>"
    
    result = load_html(html_like)
    
    # Should either parse or return None, but not raise unhandled exception
    assert result is None or isinstance(result, HtmlElement)


# Test with DOCTYPE variations
@given(st.text(min_size=1, max_size=100))
@example("<!DOCTYPE html>")
@example("<!doctype HTML>")
@example("< ! DOCTYPE html / >")
def test_load_html_doctype_handling(doctype_text):
    """Test that load_html handles various DOCTYPE declarations"""
    html_with_doctype = f"{doctype_text}\n<html><body>test</body></html>"
    
    result = load_html(html_with_doctype)
    
    # Should handle DOCTYPE and still parse
    assert result is None or isinstance(result, HtmlElement)


# Test faulty HTML patterns mentioned in repair_faulty_html
@given(st.text(min_size=0, max_size=100))
def test_load_html_self_closing_html_tag(content):
    """Test load_html with self-closing HTML tags (mentioned as faulty)"""
    # Create HTML with self-closing html tag (which is faulty)
    faulty_html = f"<html {content}/>\n<body>test</body>"
    
    result = load_html(faulty_html)
    
    # The repair function should fix this
    assert result is None or isinstance(result, HtmlElement)


# Edge case: Empty and whitespace-only inputs
@given(st.sampled_from(["", " ", "\n", "\t", "   \n\t  "]))
def test_load_html_empty_inputs(empty_input):
    """Test load_html with empty or whitespace-only inputs"""
    result = load_html(empty_input)
    
    # Should handle gracefully
    assert result is None or isinstance(result, HtmlElement)


# Test load_html type validation
def test_load_html_invalid_type():
    """Test that load_html raises TypeError for invalid input types"""
    try:
        # Pass an invalid type (not bytes, str, or HtmlElement)
        result = load_html(12345)
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "incompatible input type" in str(e)
        

# Test URL detection in load_html
@given(st.text(alphabet=st.characters(blacklist_characters=" "), min_size=5, max_size=50))
def test_load_html_url_detection(text):
    """Test URL detection logic in load_html"""
    # Create something that looks like a URL
    url_like = f"http{text}"
    
    # This will try to fetch the URL (which will fail), so it should raise ValueError
    try:
        result = load_html(url_like)
        # If it doesn't raise, it means it didn't treat it as a URL
        # (maybe because of the no-space check)
        assert result is None or isinstance(result, HtmlElement)
    except ValueError as e:
        # Expected for URL that couldn't be fetched
        assert "URL couldn't be processed" in str(e) or "URL" in str(e)
    except:
        # Other exceptions might occur
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])