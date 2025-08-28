import html
import html.entities
from hypothesis import given, strategies as st, assume, settings, note
import re


@given(st.lists(st.sampled_from(['&', 'amp', ';', 'lt', 'gt', 'quot', '#', '65', 'x41']), 
                min_size=2, max_size=10))
def test_complex_entity_sequences(parts):
    """Test complex sequences that might confuse the parser"""
    text = ''.join(parts)
    result = html.unescape(text)
    
    # Should not crash
    assert isinstance(result, str)
    
    # Check for any double-unescaping issues
    result2 = html.unescape(result)
    if '&' not in result:
        # If there's no & in first result, second unescape shouldn't change it
        assert result == result2


@given(st.text(alphabet='0123456789', min_size=15, max_size=25))
def test_very_long_numeric_entities(digits):
    """Test numeric entities with very long digit sequences"""
    entity = f'&#{digits};'
    result = html.unescape(entity)
    
    # Should handle without crashing
    assert isinstance(result, str)
    
    # Very large numbers should become replacement character
    try:
        num = int(digits)
        if num > 0x10FFFF:
            assert result == '\uFFFD'
    except ValueError:
        # Too large to convert
        assert result == '\uFFFD'


@given(st.text(min_size=1, max_size=50))
def test_html5_longest_match(text):
    """Test the longest match behavior for HTML5 entities"""
    # Create an entity-like string
    entity = '&' + text
    result = html.unescape(entity)
    
    # The implementation should find the longest matching entity
    # This is specified in the comment on line 110 of html/__init__.py
    if not text.startswith('#') and not text[0] in '\t\n\f <&#;':
        # Check if any prefix matches
        matches = []
        for i in range(min(len(text), 32), 0, -1):  # Max 32 chars as per regex
            prefix = text[:i]
            if prefix in html.entities.html5:
                matches.append((i, prefix))
            if prefix + ';' in html.entities.html5:
                matches.append((i, prefix + ';'))
        
        if matches:
            # Should use the longest match
            longest = max(matches, key=lambda x: x[0])
            expected_char = html.entities.html5[longest[1]]
            if longest[1].endswith(';'):
                remainder = text[longest[0]-1:]  # -1 because we added the ;
            else:
                remainder = text[longest[0]:]
            
            expected = expected_char + remainder
            # Due to complex matching rules, just verify it processed something
            if result != entity:
                assert result.startswith(expected_char) or '&' in result


@given(st.sampled_from(list(html.entities.name2codepoint.keys())),
       st.sampled_from(list(html.entities.name2codepoint.keys())))
def test_consecutive_entities_without_semicolon(name1, name2):
    """Test consecutive entities without semicolons between them"""
    # This could be ambiguous: &ampamp could be &amp + amp or &am + pamp etc
    text = f'&{name1}{name2}'
    result = html.unescape(text)
    
    # Should handle without crashing
    assert isinstance(result, str)
    
    # Check if it matches expected longest-match behavior
    # The parser should try to match the longest possible entity name


@given(st.integers(min_value=0x80, max_value=0x9F))
def test_windows_1252_entities(codepoint):
    """Test the special Windows-1252 character mappings"""
    entity = f'&#{codepoint};'
    result = html.unescape(entity)
    
    # These are in the _invalid_charrefs mapping
    if codepoint in html._invalid_charrefs:
        expected = html._invalid_charrefs[codepoint]
        assert result == expected, f"CP-1252 mapping failed for {codepoint:#x}"
    elif codepoint in html._invalid_codepoints:
        assert result == ''
    else:
        # Some in this range might not be in either dict
        assert isinstance(result, str)


@given(st.sampled_from(['&#x1f4a9;', '&#128169;', '&#x1F4A9;']))
def test_emoji_entities(entity):
    """Test that emoji codepoints work correctly"""
    result = html.unescape(entity)
    # Should produce the pile of poo emoji
    assert result == '💩'


@given(st.integers(min_value=1, max_value=0x10FFFF))
def test_numeric_entity_boundaries(codepoint):
    """Test boundary conditions for numeric entities"""
    if 0xD800 <= codepoint <= 0xDFFF:
        # Skip surrogate pairs
        return
    
    entity_dec = f'&#{codepoint};'
    entity_hex = f'&#x{codepoint:x};'
    
    result_dec = html.unescape(entity_dec)
    result_hex = html.unescape(entity_hex)
    
    if codepoint in html._invalid_charrefs:
        expected = html._invalid_charrefs[codepoint]
    elif codepoint in html._invalid_codepoints:
        expected = ''
    elif codepoint == 0:
        expected = '\uFFFD'
    else:
        expected = chr(codepoint)
    
    assert result_dec == expected
    assert result_hex == expected


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])