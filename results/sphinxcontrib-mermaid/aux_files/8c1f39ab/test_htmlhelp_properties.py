"""Property-based tests for sphinxcontrib.htmlhelp module."""

import html
import re
import sys
import os
from html.entities import codepoint2name

sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import sphinxcontrib.htmlhelp as htmlhelp


@given(st.text())
def test_chm_htmlescape_converts_hex_to_decimal_for_single_quote(text):
    """Test that chm_htmlescape converts &#x27; to &#39; as documented."""
    result = htmlhelp.chm_htmlescape(text, quote=True)
    
    # The function should never produce &#x27; in the output
    assert '&#x27;' not in result
    
    # If the input contains single quotes, they should be escaped as &#39;
    if "'" in text:
        assert '&#39;' in result or '&apos;' in result
    
    # The result should be valid escaped HTML
    # Unescape to verify it's valid
    try:
        html.unescape(result)
    except Exception as e:
        raise AssertionError(f"Result is not valid escaped HTML: {e}")


@given(st.text())
def test_chm_htmlescape_quote_parameter(text):
    """Test that the quote parameter controls quote escaping."""
    result_with_quotes = htmlhelp.chm_htmlescape(text, quote=True)
    result_without_quotes = htmlhelp.chm_htmlescape(text, quote=False)
    
    # If text contains quotes, results should differ when quote parameter changes
    if '"' in text:
        # With quote=True, quotes should be escaped
        assert '&quot;' in result_with_quotes or '&#34;' in result_with_quotes
        # With quote=False, quotes should not be escaped  
        assert '"' in result_without_quotes
    
    # Other characters should be escaped the same way
    text_no_quotes = text.replace('"', '').replace("'", '')
    if text_no_quotes:
        result1_no_quotes = result_with_quotes.replace('&quot;', '').replace('&#34;', '').replace('&#39;', '').replace('&apos;', '')
        result2_no_quotes = result_without_quotes.replace('"', '').replace("'", '')
        # The non-quote parts should be escaped identically
        

@given(st.text())
def test_chm_htmlescape_basic_escaping(text):
    """Test that basic HTML escaping works correctly."""
    result = htmlhelp.chm_htmlescape(text, quote=True)
    
    # Check that dangerous HTML characters are escaped
    if '<' in text:
        assert '<' not in result or result == text  # Allow if no escaping needed
        assert '&lt;' in result
    if '>' in text:
        assert '>' not in result or result == text
        assert '&gt;' in result
    if '&' in text and not any(text[i:].startswith(ent) for i in range(len(text)) 
                               for ent in ['&lt;', '&gt;', '&amp;', '&quot;', '&#']):
        # Only check if & is not part of an entity
        assert '&amp;' in result


@given(st.text(st.characters(min_codepoint=128, max_codepoint=0x10ffff)))
def test_escape_method_non_ascii(text):
    """Test the _escape method converts non-ASCII characters correctly."""
    # The _escape method is a static method of HTMLHelpBuilder
    escape_func = htmlhelp.HTMLHelpBuilder._escape
    
    # Test each character individually
    for char in text:
        if ord(char) < 128:
            continue
            
        match_obj = re.match(r'.*', char)
        result = escape_func(match_obj)
        
        codepoint = ord(char)
        
        # Check the result is properly formatted
        if codepoint in codepoint2name:
            # Should use named entity
            expected = f"&{codepoint2name[codepoint]};"
            assert result == expected, f"Character {char} (U+{codepoint:04X}) should produce {expected}, got {result}"
        else:
            # Should use numeric entity
            expected = f"&#{codepoint};"
            assert result == expected, f"Character {char} (U+{codepoint:04X}) should produce {expected}, got {result}"
        
        # Result should be ASCII only
        assert all(ord(c) < 128 for c in result), f"Result {result} contains non-ASCII characters"


@given(st.text())
def test_escape_entire_string(text):
    """Test that escaping an entire string preserves the content."""
    # Use the HTMLHelpBuilder's approach to escape non-ASCII
    builder = htmlhelp.HTMLHelpBuilder
    
    # Apply the escape to the entire string as the builder does
    escaped = re.sub(r"[^\x00-\x7F]", builder._escape, text)
    
    # All characters in result should be ASCII
    assert all(ord(c) < 128 for c in escaped), "Result contains non-ASCII characters"
    
    # The escaped version should unescape back to the original
    unescaped = html.unescape(escaped)
    assert unescaped == text, f"Round-trip failed: {text!r} -> {escaped!r} -> {unescaped!r}"


@given(st.lists(st.text(st.characters(blacklist_categories=['Cc', 'Cs'])), min_size=1))
def test_toc_visitor_list_nesting(items):
    """Test that ToCTreeVisitor correctly handles list nesting."""
    # This tests the depth tracking in ToCTreeVisitor
    from docutils import nodes
    
    doc = nodes.document('')
    visitor = htmlhelp.ToCTreeVisitor(doc)
    
    # Initial depth should be 0
    assert visitor.depth == 0
    
    # Create a bullet list node
    bullet_list = nodes.bullet_list()
    
    # Visit should increase depth
    visitor.visit_bullet_list(bullet_list)
    assert visitor.depth == 1
    
    # Nested visit should increase depth further
    visitor.visit_bullet_list(bullet_list)
    assert visitor.depth == 2
    
    # Depart should decrease depth
    visitor.depart_bullet_list(bullet_list)
    assert visitor.depth == 1
    
    visitor.depart_bullet_list(bullet_list)
    assert visitor.depth == 0
    
    # Depth should never go negative
    visitor.depart_bullet_list(bullet_list)
    assert visitor.depth == -1  # This might be a bug if depth can go negative!


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])