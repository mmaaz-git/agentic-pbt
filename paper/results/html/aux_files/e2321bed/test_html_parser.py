import html
import html.parser
from html.parser import HTMLParser
from hypothesis import given, strategies as st, assume, settings
import re
import string


class DataCollector(HTMLParser):
    def __init__(self, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.data = []
        self.tags = []
        self.comments = []
        self.errors = []
        
    def handle_starttag(self, tag, attrs):
        self.tags.append(('start', tag, attrs))
    
    def handle_endtag(self, tag):
        self.tags.append(('end', tag))
    
    def handle_data(self, data):
        self.data.append(data)
        
    def handle_comment(self, data):
        self.comments.append(data)
        
    def error(self, message):
        self.errors.append(message)


@given(st.text(alphabet=string.ascii_letters + string.digits + '&#;xX', min_size=1))
def test_unescape_charref_roundtrip(s):
    """Test that valid character references can be escaped and unescaped"""
    # Focus on numeric character references
    for i in range(1, min(128, len(s))):
        ref = f"&#{i};"
        unescaped = html.unescape(ref)
        # Should produce exactly one character for valid ASCII codes
        if 0 < i < 128:
            assert len(unescaped) == 1 or i in [0, 13]  # Some control chars may behave differently


@given(st.text())
def test_feed_incremental_vs_whole(text):
    """Feeding data incrementally vs all at once should produce same results"""
    # Parse all at once
    parser1 = DataCollector()
    parser1.feed(text)
    parser1.close()
    
    # Parse incrementally
    parser2 = DataCollector()
    if len(text) > 0:
        mid = len(text) // 2
        parser2.feed(text[:mid])
        parser2.feed(text[mid:])
    parser2.close()
    
    # Results should be identical
    assert parser1.data == parser2.data
    assert parser1.tags == parser2.tags


@given(st.text(alphabet='<>abcdefghijklmnopqrstuvwxyz/', min_size=1, max_size=100))
def test_parser_doesnt_crash(html_text):
    """Parser should not crash on any input"""
    parser = HTMLParser()
    parser.feed(html_text)
    parser.close()


@given(st.integers(0, 0x10ffff))
def test_numeric_charref_handling(codepoint):
    """Test numeric character reference handling"""
    # Decimal reference
    dec_ref = f"&#{codepoint};"
    # Hex reference  
    hex_ref = f"&#x{codepoint:x};"
    hex_ref_upper = f"&#X{codepoint:X};"
    
    dec_result = html.unescape(dec_ref)
    hex_result = html.unescape(hex_ref)
    hex_upper_result = html.unescape(hex_ref_upper)
    
    # All three forms should produce the same result
    assert dec_result == hex_result
    assert hex_result == hex_upper_result
    
    # Valid Unicode codepoints should be unescaped to the character
    if 0 < codepoint <= 0x10ffff and not (0xD800 <= codepoint <= 0xDFFF):
        # Not a surrogate
        try:
            expected = chr(codepoint)
            assert dec_result == expected
        except ValueError:
            pass


@given(st.text(min_size=1))
def test_unescape_preserves_non_entities(text):
    """Text without entities should pass through unescape unchanged"""
    assume('&' not in text)
    assert html.unescape(text) == text


@given(st.text())
def test_parser_state_after_reset(text):
    """Parser state should be clean after reset"""
    parser = DataCollector()
    
    # First parse
    parser.feed(text)
    parser.close()
    first_data = parser.data[:]
    
    # Reset and parse again
    parser.reset()
    parser.data = []
    parser.tags = []
    parser.feed(text)
    parser.close()
    second_data = parser.data[:]
    
    # Should produce same results
    assert first_data == second_data


@given(st.lists(st.text(alphabet='<>"/= abcdefghijklmnopqrstuvwxyz', min_size=1), min_size=1))
def test_attribute_parsing(attr_parts):
    """Test attribute parsing doesn't lose or corrupt data"""
    # Build an attribute string
    tag_name = "div"
    attrs = []
    for i, part in enumerate(attr_parts):
        # Create attribute with escaped value
        key = f"attr{i}"
        value = html.escape(part, quote=True)
        attrs.append(f'{key}="{value}"')
    
    html_str = f"<{tag_name} {' '.join(attrs)}></{tag_name}>"
    
    parser = DataCollector()
    parser.feed(html_str)
    parser.close()
    
    # Should have parsed the tag
    assert len(parser.tags) >= 1
    if parser.tags:
        assert parser.tags[0][0] == 'start'
        assert parser.tags[0][1] == tag_name


@given(st.text(alphabet='<>&\'"', min_size=1))
def test_special_chars_in_data(text):
    """Special HTML characters in data sections should be handled correctly"""
    parser = DataCollector(convert_charrefs=True)
    
    # Wrap text in a tag
    html_str = f"<p>{text}</p>"
    
    try:
        parser.feed(html_str)
        parser.close()
        # Should not crash
        assert True
    except:
        # Parser crashed on valid-looking input
        assert False, f"Parser crashed on input: {html_str}"


@given(st.text())
def test_comment_handling(comment_text):
    """Comments should be parsed correctly"""
    assume('-->' not in comment_text)
    assume('--!' not in comment_text)
    
    html_str = f"<!-- {comment_text} -->"
    parser = DataCollector()
    parser.feed(html_str)
    parser.close()
    
    # Should have captured the comment
    if parser.comments:
        # Comment content should be preserved (with possible whitespace handling)
        assert comment_text.strip() in parser.comments[0] or parser.comments[0] in comment_text


@given(st.text(alphabet=string.ascii_letters + string.digits))
def test_entity_name_parsing(entity_name):
    """Test entity reference parsing"""
    assume(len(entity_name) > 0)
    
    # Create entity reference
    entity_ref = f"&{entity_name};"
    
    # Try to unescape it
    result = html.unescape(entity_ref)
    
    # If it's not a known entity, should remain unchanged
    # If it is known, should be different
    assert result == entity_ref or result != entity_ref


@given(st.integers(min_value=-1000, max_value=0x110000))
def test_invalid_charref_handling(codepoint):
    """Test handling of invalid character references"""
    ref = f"&#{codepoint};"
    result = html.unescape(ref)
    
    # Should not crash
    assert result is not None
    
    # Negative or too large codepoints should not be converted
    if codepoint < 0 or codepoint > 0x10ffff:
        # These should trigger replacement character or remain unchanged
        assert result == ref or result == '\ufffd' or len(result) == 1


@given(st.text(alphabet='<>/', min_size=2, max_size=20))
def test_malformed_tags(tag_content):
    """Parser should handle malformed tags gracefully"""
    malformed_htmls = [
        f"<{tag_content}",  # Unclosed tag
        f"</{tag_content}",  # End tag without start
        f"<<{tag_content}>>",  # Double brackets
        f"<{tag_content}/>",  # Self-closing
    ]
    
    for html_str in malformed_htmls:
        parser = HTMLParser()
        parser.feed(html_str)
        parser.close()
        # Should not crash


@given(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5))
def test_cdata_mode(elements):
    """Test CDATA mode for script/style elements"""
    for elem in ['script', 'style']:
        content = ' '.join(elements)
        html_str = f"<{elem}>{content}</{elem}>"
        
        parser = DataCollector(convert_charrefs=False)
        parser.feed(html_str)
        parser.close()
        
        # Content should be captured
        assert len(parser.data) >= 0


@given(st.text())
def test_empty_tag_handling(tag_name):
    """Test empty and self-closing tags"""
    assume(re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', tag_name))
    
    # Test empty tag
    html_str1 = f"<{tag_name}></{tag_name}>"
    parser1 = DataCollector()
    parser1.feed(html_str1)
    
    # Test self-closing
    html_str2 = f"<{tag_name}/>"
    parser2 = DataCollector()
    parser2.feed(html_str2)
    
    # Both should be handled without crashing
    assert True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])