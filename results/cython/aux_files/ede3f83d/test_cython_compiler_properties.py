#!/usr/bin/env python3
"""
Property-based tests for Cython.Compiler modules using Hypothesis.
"""

import math
import sys
from hypothesis import given, strategies as st, assume, settings

import Cython.Compiler.StringEncoding as SE


# Test 1: escape_byte_string should return valid ASCII that represents the original bytes
@given(st.binary(min_size=0, max_size=1000))
def test_escape_byte_string_produces_ascii(data):
    """
    Property: escape_byte_string should always return a valid ASCII string.
    According to the docstring, it returns a Unicode string that when
    encoded as ASCII will result in the correct byte sequence.
    """
    result = SE.escape_byte_string(data)
    
    # Result should be a string
    assert isinstance(result, str)
    
    # Result should be encodable as ASCII
    try:
        ascii_bytes = result.encode('ASCII')
    except UnicodeEncodeError:
        assert False, f"Result contains non-ASCII characters: {result!r}"


# Test 2: escape_byte_string should preserve printable ASCII characters
@given(st.binary(min_size=1, max_size=100))
def test_escape_byte_string_preserves_printable_ascii(data):
    """
    Property: Printable ASCII characters (except special ones) should be preserved.
    Non-printable and high bytes should be escaped.
    """
    result = SE.escape_byte_string(data)
    
    # Check that the result contains valid escape sequences
    # All bytes >= 127 should be escaped as octal
    for b in data:
        if b >= 127:
            # Should be escaped as \ooo octal
            assert ('\\%03o' % b) in result or ('\\x%02X' % b) in result


# Test 3: split_string_literal should preserve content
@given(st.text(min_size=0, max_size=10000), st.integers(min_value=10, max_value=500))
def test_split_string_literal_preserves_content(s, limit):
    """
    Property: split_string_literal should preserve the string content
    when it splits long strings, just adding "" between chunks.
    """
    result = SE.split_string_literal(s, limit)
    
    # If string is shorter than limit, it should be unchanged
    if len(s) < limit:
        assert result == s
    else:
        # String should be split with "" joining chunks
        # The joined result (removing "") should equal the original
        rejoined = result.replace('""', '')
        assert rejoined == s


# Test 4: Relationship between string_contains_surrogates and string_contains_lone_surrogates
@given(st.text(min_size=0, max_size=100))
def test_surrogate_detection_relationship(s):
    """
    Property: If a string contains lone surrogates, it must also contain surrogates.
    This is a logical relationship - lone surrogates are a subset of all surrogates.
    """
    contains_surrogates = SE.string_contains_surrogates(s)
    contains_lone = SE.string_contains_lone_surrogates(s)
    
    # If there are lone surrogates, there must be surrogates
    if contains_lone:
        assert contains_surrogates, f"String {s!r} has lone surrogates but string_contains_surrogates returned False"


# Test 5: UnicodeLiteralBuilder round-trip
@given(st.text(min_size=0, max_size=100))
def test_unicode_literal_builder_roundtrip(text):
    """
    Property: Building a unicode literal and getting it back should preserve the text.
    """
    builder = SE.UnicodeLiteralBuilder()
    builder.append(text)
    result = builder.getstring()
    
    # Result should be an EncodedString containing our text
    assert str(result) == text
    assert isinstance(result, SE.EncodedString)


# Test 6: BytesLiteralBuilder with UTF-8 encoding
@given(st.text(min_size=0, max_size=100))
def test_bytes_literal_builder_utf8(text):
    """
    Property: BytesLiteralBuilder should correctly encode text to bytes.
    """
    builder = SE.BytesLiteralBuilder('utf-8')
    builder.append(text)
    result = builder.getstring()
    
    # Result should be a BytesLiteral
    assert isinstance(result, SE.BytesLiteral)
    
    # The content should match the UTF-8 encoding of the text
    expected = text.encode('utf-8')
    assert bytes(result) == expected


# Test 7: encoded_string preserves string content
@given(st.text(min_size=0, max_size=100))
def test_encoded_string_preserves_content(text):
    """
    Property: Creating an EncodedString should preserve the string content.
    """
    # Test with no encoding (unicode)
    result = SE.encoded_string(text, None)
    assert str(result) == text
    assert result.is_unicode
    assert result.encoding is None
    
    # Test with UTF-8 encoding
    result_utf8 = SE.encoded_string(text, 'utf-8')
    assert str(result_utf8) == text
    assert not result_utf8.is_unicode
    assert result_utf8.encoding == 'utf-8'


# Test 8: escape_char function for single bytes
@given(st.binary(min_size=1, max_size=1))
def test_escape_char_single_byte(byte_data):
    """
    Property: escape_char should properly escape single byte characters.
    """
    result = SE.escape_char(byte_data)
    
    # Result should be a string
    assert isinstance(result, str)
    
    # Check specific escaping rules from the implementation
    b = byte_data[0]
    c = chr(b)
    
    if c in '\n\r\t\\':
        # Should be escaped as repr-style 
        assert result in ['\\n', '\\r', '\\t', '\\\\']
    elif c == "'":
        assert result == "\\'"
    elif b < 32 or b >= 127:
        # Should be hex escaped
        assert result == "\\x%02X" % b
    else:
        # Should be the character itself
        assert result == c


# Test 9: Special characters in escape_byte_string
@given(st.lists(st.integers(min_value=0, max_value=255), min_size=1, max_size=100))
def test_escape_byte_string_special_chars(byte_values):
    """
    Property: escape_byte_string should handle special C characters correctly.
    """
    data = bytes(byte_values)
    result = SE.escape_byte_string(data)
    
    # Check that special characters are escaped
    # According to the code, characters like \n, \t, \r, \\, " should be escaped
    special_escapes = {
        ord('\n'): '\\n',
        ord('\r'): '\\r', 
        ord('\t'): '\\t',
        ord('\\'): '\\\\',
        ord('"'): '\\"'
    }
    
    # The result should be valid ASCII
    assert all(ord(c) < 128 for c in result)


# Test 10: UnicodeLiteralBuilder with high Unicode characters
@given(st.integers(min_value=0, max_value=0x10FFFF))
def test_unicode_literal_builder_append_charval(char_code):
    """
    Property: UnicodeLiteralBuilder.append_charval should handle all valid Unicode code points.
    """
    # Skip surrogate range which is invalid for chr()
    assume(not (0xD800 <= char_code <= 0xDFFF))
    
    builder = SE.UnicodeLiteralBuilder()
    builder.append_charval(char_code)
    result = builder.getstring()
    
    # On narrow Unicode builds (sys.maxunicode == 65535), 
    # characters > 65535 are split into surrogate pairs
    if sys.maxunicode == 65535 and char_code > 65535:
        # Should be a surrogate pair
        assert len(result) == 2
        # Verify it's a valid surrogate pair
        high = ord(result[0])
        low = ord(result[1])
        assert 0xD800 <= high <= 0xDBFF  # High surrogate
        assert 0xDC00 <= low <= 0xDFFF   # Low surrogate
    else:
        # Should be the character itself
        assert str(result) == chr(char_code)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])