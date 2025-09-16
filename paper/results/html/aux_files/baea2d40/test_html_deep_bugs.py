import html
from hypothesis import given, strategies as st, assume, settings
import sys

# Test for potential issues with character reference parsing edge cases
@given(st.text(alphabet='0123456789', min_size=20, max_size=100))
def test_numeric_overflow_edge_cases(digits):
    """Test potential issues with very large numeric references"""
    entity = f'&#{digits};'
    try:
        result = html.unescape(entity)
        # Should handle gracefully
        assert result == '\uFFFD'
    except:
        # If it raises an exception, that's a bug
        assert False, f"Exception raised for large numeric entity: {entity}"

# Test for off-by-one errors in entity matching
def test_entity_boundary_matching():
    """Test HTML5 spec partial entity matching edge cases"""
    # Test cases where partial matching might have off-by-one errors
    
    # The 'not' entity exists, so 'no' should not match it
    assert html.unescape('&no') == '&no'
    assert html.unescape('&not') == '¬'
    
    # Test increasingly long prefixes
    assert html.unescape('&n') == '&n'
    assert html.unescape('&no') == '&no'
    assert html.unescape('&not') == '¬'
    assert html.unescape('&noti') == '¬i'
    assert html.unescape('&notit') == '¬it'

# Test concurrent modification scenarios (string immutability should handle this)
@given(st.text())
def test_escape_immutability(s):
    """Ensure escape doesn't modify the original string"""
    original = s
    escaped = html.escape(s)
    assert s == original  # String should be unchanged
    assert id(s) == id(original)  # Same object

# Test for issues with specific invalid codepoint replacements
def test_invalid_charref_replacements():
    """Test the special replacements in _invalid_charrefs"""
    # From lines 30-65 of the source
    special_replacements = {
        0x00: '\ufffd',
        0x0d: '\r',
        0x80: '\u20ac',
        0x82: '\u201a',
        0x83: '\u0192',
        0x84: '\u201e',
        0x85: '\u2026',
        0x86: '\u2020',
        0x87: '\u2021',
        0x88: '\u02c6',
        0x89: '\u2030',
        0x8a: '\u0160',
        0x8b: '\u2039',
        0x8c: '\u0152',
        0x8e: '\u017d',
        0x91: '\u2018',
        0x92: '\u2019',
        0x93: '\u201c',
        0x94: '\u201d',
        0x95: '\u2022',
        0x96: '\u2013',
        0x97: '\u2014',
        0x98: '\u02dc',
        0x99: '\u2122',
        0x9a: '\u0161',
        0x9b: '\u203a',
        0x9c: '\u0153',
        0x9e: '\u017e',
        0x9f: '\u0178',
    }
    
    for codepoint, expected in special_replacements.items():
        entity = f'&#{codepoint};'
        result = html.unescape(entity)
        assert result == expected, f"Failed for codepoint 0x{codepoint:02x}: got {repr(result)}, expected {repr(expected)}"

# Test regex pattern edge cases
@given(st.text(min_size=1, max_size=100))
def test_ampersand_heavy_strings(text):
    """Test strings with many ampersands"""
    # Create string with ampersands everywhere
    amp_text = '&'.join(text)
    escaped = html.escape(amp_text)
    unescaped = html.unescape(escaped)
    assert unescaped == amp_text

# Test entity names up to max length (32 chars according to regex)
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=33, max_size=40))
def test_entity_name_length_limit(long_name):
    """Test the 32 character limit for entity names"""
    entity = f'&{long_name};'
    result = html.unescape(entity)
    # Should not match as entity (too long)
    assert result == entity

# Test for consistency between escape with different quote values
@given(st.text())
def test_quote_consistency(s):
    """Ensure quote parameter works correctly with various types"""
    # Test with different truthy/falsy values
    escaped_true = html.escape(s, quote=True)
    escaped_1 = html.escape(s, quote=1)
    escaped_obj = html.escape(s, quote=object())  # Any object is truthy
    
    escaped_false = html.escape(s, quote=False)
    escaped_0 = html.escape(s, quote=0)
    escaped_none = html.escape(s, quote=None)
    escaped_empty = html.escape(s, quote=[])  # Empty list is falsy
    
    # Truthy values should all produce same result
    assert escaped_true == escaped_1 == escaped_obj
    
    # Falsy values should all produce same result
    assert escaped_false == escaped_0 == escaped_none == escaped_empty

# Test interaction between different entity types in same string
@given(st.text())
def test_mixed_entity_types(prefix):
    """Test strings containing both named and numeric entities"""
    mixed = prefix + '&amp;&#65;&lt;&#x42;&gt;'
    result = html.unescape(mixed)
    expected = prefix + '&A<B>'
    assert result == expected

# Look for issues with the regex matching
def test_regex_edge_cases():
    """Test edge cases in the character reference regex pattern"""
    # The regex: r'&(#[0-9]+;?|#[xX][0-9a-fA-F]+;?|[^\t\n\f <&#;]{1,32};?)'
    
    # Test optional semicolon behavior
    assert html.unescape('&#65') == 'A'
    assert html.unescape('&#65;') == 'A'
    assert html.unescape('&#x41') == 'A'
    assert html.unescape('&#x41;') == 'A'
    
    # Test case insensitivity of X
    assert html.unescape('&#x41;') == 'A'
    assert html.unescape('&#X41;') == 'A'
    
    # Test invalid hex digits are not consumed
    assert html.unescape('&#xGG;') == '&#xGG;'
    assert html.unescape('&#x4G;') == '\x04G;'  # Parses 4, leaves G;

# Focus on the _replace_charref logic
def test_replace_charref_edge_cases():
    """Test edge cases in character reference replacement"""
    # Test surrogate range handling (0xD800-0xDFFF)
    for cp in [0xD800, 0xD900, 0xDC00, 0xDFFF]:
        entity = f'&#{cp};'
        result = html.unescape(entity)
        assert result == '\uFFFD', f"Surrogate 0x{cp:04x} should be replaced with U+FFFD"
    
    # Test just outside surrogate range
    assert html.unescape('&#55295;') != '\uFFFD'  # 0xD7FF
    assert html.unescape('&#57344;') != '\uFFFD'  # 0xE000
    
    # Test boundary at 0x10FFFF
    assert html.unescape('&#1114111;') == '\U0010FFFF'  # Max valid
    assert html.unescape('&#1114112;') == '\uFFFD'  # Just over max

# Test for any issues with empty/whitespace entity names
@given(st.text(alphabet=' \t\n\r'))
def test_whitespace_in_entities(ws):
    """Test entities with whitespace"""
    if ws:
        entity = f'&{ws};'
        result = html.unescape(entity)
        # Whitespace should not be recognized as entity name
        assert result == entity

# Stress test the longest valid entity
def test_longest_entity_stress():
    """Stress test with the longest named entity"""
    longest = 'CounterClockwiseContourIntegral'
    
    # Valid entity
    assert html.unescape(f'&{longest};') == '∳'
    
    # One char short - should not match
    assert html.unescape(f'&{longest[:-1]};') == f'&{longest[:-1]};'
    
    # Extra char - should partially match
    assert html.unescape(f'&{longest}x;') == f'∳x;'

# Test escape/unescape with strings containing null bytes
@given(st.text())
def test_null_bytes(s):
    """Test handling of null bytes"""
    text_with_null = s + '\x00' + s
    escaped = html.escape(text_with_null)
    unescaped = html.unescape(escaped)
    assert unescaped == text_with_null

# Look for discrepancies in how different types of entities are handled
def test_entity_type_consistency():
    """Ensure different representations of same character are handled consistently"""
    # Different ways to represent 'A' (65)
    representations = [
        '&#65;',
        '&#065;',
        '&#0065;',
        '&#00065;',
        '&#000065;',
        '&#x41;',
        '&#x041;',
        '&#x0041;',
        '&#X41;',
        '&#X041;',
        '&#X0041;',
    ]
    
    for rep in representations:
        result = html.unescape(rep)
        assert result == 'A', f"Failed for {rep}: got {repr(result)}"

# Test interaction with Python's string encoding
@given(st.text())
def test_unicode_normalization(s):
    """Test that escape/unescape preserves Unicode normalization"""
    import unicodedata
    
    # Test with different normalizations
    for form in ['NFC', 'NFD', 'NFKC', 'NFKD']:
        normalized = unicodedata.normalize(form, s)
        escaped = html.escape(normalized)
        unescaped = html.unescape(escaped)
        
        # Should preserve the normalization form
        assert unescaped == normalized

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])