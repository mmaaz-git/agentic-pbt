import html
import html.entities
from hypothesis import given, strategies as st, assume, settings, note
import re


@given(st.text(min_size=1, max_size=100))
@settings(max_examples=1000)
def test_unescape_consistency(text):
    """Test that unescaping is idempotent after first application"""
    if '&' not in text:
        return
    
    unescaped_once = html.unescape(text)
    unescaped_twice = html.unescape(unescaped_once)
    
    if unescaped_once != unescaped_twice:
        note(f"Input: {text!r}")
        note(f"After 1 unescape: {unescaped_once!r}")
        note(f"After 2 unescapes: {unescaped_twice!r}")
        
        # Check if this could be a legitimate double-encoding case
        if '&' in unescaped_once:
            # This might be legitimate if the original had double-encoded entities
            pass
        else:
            # If there's no & in the first result, second unescape shouldn't change anything
            assert unescaped_once == unescaped_twice


@given(st.integers(min_value=-2**63, max_value=2**63))
def test_large_numeric_entities(num):
    """Test very large numeric character references"""
    decimal_entity = f'&#{num};'
    result = html.unescape(decimal_entity)
    
    if num < 0:
        # Negative numbers should not be processed
        assert result == decimal_entity
    elif num > 0x10FFFF:
        # Out of Unicode range should give replacement character
        assert result == '\uFFFD'
    elif 0xD800 <= num <= 0xDFFF:
        # Surrogate pairs should give replacement character
        assert result == '\uFFFD'


@given(st.text(alphabet='0123456789abcdefABCDEFxX', min_size=1, max_size=20))
def test_malformed_hex_entities(text):
    """Test malformed hexadecimal entities"""
    entity = '&#' + text + ';'
    result = html.unescape(entity)
    
    # Check if it's a valid hex entity
    if text.startswith('x') or text.startswith('X'):
        hex_part = text[1:]
        try:
            value = int(hex_part, 16)
            if value > 0x10FFFF:
                assert result == '\uFFFD'
            elif 0xD800 <= value <= 0xDFFF:
                assert result == '\uFFFD'
            elif value == 0:
                assert result == '\uFFFD'
            elif value in html._invalid_charrefs:
                assert result == html._invalid_charrefs[value]
            elif value in html._invalid_codepoints:
                assert result == ''
            else:
                assert result == chr(value)
        except ValueError:
            # Invalid hex should return the original entity
            assert result == entity
    else:
        # Should be treated as decimal
        try:
            value = int(text, 10)
            if value > 0x10FFFF:
                assert result == '\uFFFD'
            elif 0xD800 <= value <= 0xDFFF:
                assert result == '\uFFFD'
            elif value == 0:
                assert result == '\uFFFD'
            elif value in html._invalid_charrefs:
                assert result == html._invalid_charrefs[value]
            elif value in html._invalid_codepoints:
                assert result == ''
            else:
                assert result == chr(value)
        except ValueError:
            # Invalid decimal should return the original entity
            assert result == entity


@given(st.sampled_from(list(html.entities.html5.keys())))
def test_html5_dict_consistency(entity_name):
    """Check for any inconsistencies in the html5 dictionary"""
    value = html.entities.html5[entity_name]
    
    # Check if there are duplicate entries with different values
    if entity_name.endswith(';'):
        without_semicolon = entity_name[:-1]
        if without_semicolon in html.entities.html5:
            other_value = html.entities.html5[without_semicolon]
            assert value == other_value, f"Inconsistent: {entity_name}={value!r} vs {without_semicolon}={other_value!r}"
    
    # Check that the value is a valid string
    assert isinstance(value, str)
    assert len(value) >= 1


@given(st.text(alphabet=st.characters(blacklist_categories=['Cc', 'Cf', 'Cs', 'Co', 'Cn']), 
               min_size=1, max_size=20))
def test_escape_preserves_unicode(text):
    """Test that escape/unescape preserves Unicode characters correctly"""
    assume('\x00' not in text)
    assume(all(0xD800 > ord(c) or ord(c) > 0xDFFF for c in text))
    
    escaped = html.escape(text, quote=True)
    unescaped = html.unescape(escaped)
    
    assert unescaped == text, f"Round-trip failed for Unicode text"


@given(st.lists(st.sampled_from(['&', '#', ';', 'x', 'X'] + list('0123456789abcdefABCDEF')), 
                min_size=2, max_size=20))
def test_entity_like_sequences(chars):
    """Test sequences that look like entities but might not be"""
    text = ''.join(chars)
    result = html.unescape(text)
    
    # The unescape function should handle any input without crashing
    assert isinstance(result, str)


@given(st.text(min_size=1, max_size=50).filter(lambda x: '&' in x and ';' in x))
def test_incomplete_entities(text):
    """Test handling of incomplete entity references"""
    result = html.unescape(text)
    
    # Should not crash and should return a string
    assert isinstance(result, str)
    
    # If there's a valid entity pattern, it should be processed
    entity_pattern = re.compile(r'&([#\w]+);')
    matches = entity_pattern.findall(text)
    
    for match in matches:
        if match.startswith('#'):
            # Numeric entity
            if match[1:].startswith('x') or match[1:].startswith('X'):
                try:
                    value = int(match[2:], 16)
                    if 0 < value <= 0x10FFFF and not (0xD800 <= value <= 0xDFFF):
                        if value not in html._invalid_codepoints:
                            # Valid entity was found, result should be different from input
                            if value not in html._invalid_charrefs:
                                assert result != text
                except ValueError:
                    pass
            else:
                try:
                    value = int(match[1:], 10)
                    if 0 < value <= 0x10FFFF and not (0xD800 <= value <= 0xDFFF):
                        if value not in html._invalid_codepoints:
                            # Valid entity was found, result should be different from input
                            if value not in html._invalid_charrefs:
                                assert result != text
                except ValueError:
                    pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])