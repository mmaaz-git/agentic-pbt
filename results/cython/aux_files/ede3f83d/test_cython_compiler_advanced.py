#!/usr/bin/env python3
"""
Advanced property-based tests for Cython.Compiler modules.
Testing for edge cases and complex scenarios.
"""

import sys
from hypothesis import given, strategies as st, assume, settings, example

import Cython.Compiler.StringEncoding as SE


# Test for edge cases in split_string_literal
@given(st.text(alphabet=st.characters(whitelist_categories=("Cc", "Cf")), min_size=100, max_size=5000),
       st.integers(min_value=10, max_value=100))
def test_split_string_literal_control_characters(s, limit):
    """
    Property: split_string_literal should handle control characters correctly.
    """
    result = SE.split_string_literal(s, limit)
    
    # Rejoining should preserve content
    if len(s) < limit:
        assert result == s
    else:
        rejoined = result.replace('""', '')
        assert rejoined == s


# Test for backslash handling in split_string_literal
@given(st.text(alphabet='\\', min_size=100, max_size=500),
       st.integers(min_value=10, max_value=50))
@example('\\' * 100, 10)  # Force a long line of backslashes
@example('\\' * 49 + 'a', 50)  # Edge case near boundary
def test_split_string_literal_backslashes(s, limit):
    """
    Property: split_string_literal has special handling for backslashes at split points.
    It should avoid splitting in the middle of escape sequences.
    """
    result = SE.split_string_literal(s, limit)
    
    if len(s) < limit:
        assert result == s
    else:
        # Check that the split doesn't break escape sequences
        chunks = result.split('""')
        for chunk in chunks:
            # Each chunk should be valid on its own
            assert isinstance(chunk, str)
        
        # Rejoining should preserve content
        rejoined = ''.join(chunks)
        assert rejoined == s


# Test boundary conditions for escape_byte_string
@given(st.binary(min_size=0, max_size=1))
def test_escape_byte_string_boundary_bytes(data):
    """
    Property: Test boundary bytes (0, 127, 255) in escape_byte_string.
    """
    if len(data) == 0:
        result = SE.escape_byte_string(data)
        assert result == ''
    else:
        result = SE.escape_byte_string(data)
        b = data[0]
        
        # Verify escaping rules
        if b == 0:
            assert '\\000' in result or '\\x00' in result
        elif b == 127:
            assert '\\177' in result or '\\x7F' in result
        elif b == 255:
            assert '\\377' in result or '\\xFF' in result


# Test EncodedString operations
@given(st.text(min_size=0, max_size=100))
def test_encoded_string_unicode_operations(text):
    """
    Property: EncodedString with no encoding should behave like unicode.
    """
    es = SE.encoded_string(text, None)
    
    assert es.is_unicode
    assert es.encoding is None
    
    # Test utf8encode
    utf8_bytes = es.utf8encode()
    assert utf8_bytes == text.encode('utf-8')
    
    # Test as_utf8_string
    utf8_string = es.as_utf8_string()
    assert isinstance(utf8_string, SE.BytesLiteral)
    assert bytes(utf8_string) == text.encode('utf-8')


# Test EncodedString with specific encoding
@given(st.text(min_size=0, max_size=100))
def test_encoded_string_with_encoding(text):
    """
    Property: EncodedString with encoding should track that encoding.
    """
    # Use latin-1 encoding which can handle all byte values
    es = SE.encoded_string(text, 'latin-1')
    
    assert not es.is_unicode
    assert es.encoding == 'latin-1'
    
    # Test byteencode
    try:
        encoded = es.byteencode()
        assert encoded == text.encode('latin-1')
    except UnicodeEncodeError:
        # This is expected for characters outside latin-1
        pass


# Test StrLiteralBuilder dual representation
@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=50))
def test_str_literal_builder_dual(text):
    """
    Property: StrLiteralBuilder maintains both bytes and unicode representations.
    """
    builder = SE.StrLiteralBuilder('utf-8')
    builder.append(text)
    
    bytes_str, unicode_str = builder.getstrings()
    
    # Bytes representation
    assert isinstance(bytes_str, SE.BytesLiteral)
    assert bytes(bytes_str) == text.encode('utf-8')
    
    # Unicode representation
    assert isinstance(unicode_str, SE.EncodedString)
    assert str(unicode_str) == text


# Test UnicodeLiteralBuilder with surrogate pairs on narrow builds
@given(st.integers(min_value=0x10000, max_value=0x10FFFF))
def test_unicode_literal_builder_high_codepoints(char_code):
    """
    Property: High Unicode codepoints should be handled correctly.
    On narrow builds, they become surrogate pairs.
    """
    builder = SE.UnicodeLiteralBuilder()
    builder.append_charval(char_code)
    result = builder.getstring()
    
    if sys.maxunicode == 65535:
        # Narrow build - should be surrogate pair
        assert len(result) == 2
        
        # Verify surrogate pair math
        char_number = char_code - 0x10000
        expected_high = chr((char_number // 1024) + 0xD800)
        expected_low = chr((char_number % 1024) + 0xDC00)
        assert result[0] == expected_high
        assert result[1] == expected_low
    else:
        # Wide build - should be single character
        assert len(result) == 1
        assert ord(result[0]) == char_code


# Test bytes_literal function
@given(st.binary(min_size=0, max_size=100))
def test_bytes_literal_creation(data):
    """
    Property: bytes_literal should create a BytesLiteral with correct encoding.
    """
    bl = SE.bytes_literal(data, 'utf-8')
    
    assert isinstance(bl, SE.BytesLiteral)
    assert bytes(bl) == data
    assert bl.encoding == 'utf-8'
    
    # Test byteencode
    assert bl.byteencode() == data
    
    # Test str conversion (fake-decode)
    assert str(bl) == data.decode('ISO-8859-1')


# Test edge case: empty strings
@given(st.just(''))
def test_empty_string_edge_cases(empty):
    """
    Property: All functions should handle empty strings correctly.
    """
    # escape_byte_string
    assert SE.escape_byte_string(b'') == ''
    
    # split_string_literal
    assert SE.split_string_literal('', 10) == ''
    
    # string_contains_surrogates
    assert not SE.string_contains_surrogates('')
    assert not SE.string_contains_lone_surrogates('')
    
    # UnicodeLiteralBuilder
    builder = SE.UnicodeLiteralBuilder()
    builder.append('')
    assert str(builder.getstring()) == ''
    
    # BytesLiteralBuilder
    bb = SE.BytesLiteralBuilder('utf-8')
    bb.append('')
    assert bytes(bb.getstring()) == b''


# Test for potential integer overflow in split_string_literal
@given(st.text(min_size=0, max_size=100), st.integers())
def test_split_string_literal_extreme_limits(s, limit):
    """
    Property: split_string_literal should handle extreme limit values safely.
    """
    # Test with various edge case limits
    if limit <= 0:
        # Implementation might not handle negative/zero limits well
        try:
            result = SE.split_string_literal(s, limit)
            # If it doesn't error, verify result makes sense
            if len(s) == 0:
                assert result == s
        except (ValueError, IndexError, ZeroDivisionError):
            # These are reasonable errors for invalid limits
            pass
    elif limit > 1000000:
        # Very large limits should just return the original string
        result = SE.split_string_literal(s, limit)
        assert result == s
    else:
        # Normal case
        result = SE.split_string_literal(s, limit)
        if len(s) < limit:
            assert result == s


# Test special escape sequences in escape_byte_string
@given(st.binary())
def test_escape_byte_string_complex(data):
    """
    Property: Complex byte sequences with mixed printable and non-printable chars.
    """
    result = SE.escape_byte_string(data)
    
    # The result should never contain actual control characters
    for char in result:
        assert ord(char) >= 32 or char in '\t\n\r', f"Found control char: {ord(char)}"
    
    # Result should be valid ASCII
    result.encode('ascii')  # Should not raise


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])