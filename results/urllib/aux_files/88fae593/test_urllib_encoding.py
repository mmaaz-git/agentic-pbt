import urllib.parse
from hypothesis import given, strategies as st, assume, settings
import unicodedata


@given(st.text())
def test_quote_unquote_unicode_normalization(s):
    """Test if quote/unquote preserves Unicode normalization."""
    # Skip if string contains control characters
    assume(all(unicodedata.category(c)[0] != 'C' for c in s))
    
    quoted = urllib.parse.quote(s, safe='')
    unquoted = urllib.parse.unquote(quoted)
    
    # Check if Unicode normalization is preserved
    assert s == unquoted
    assert unicodedata.normalize('NFC', s) == unicodedata.normalize('NFC', unquoted)


@given(st.text())
def test_quote_plus_preserves_plus_sign(s):
    """Test quote_plus behavior with plus signs."""
    if '+' in s:
        quoted = urllib.parse.quote_plus(s, safe='')
        unquoted = urllib.parse.unquote_plus(quoted)
        assert s == unquoted


@given(st.text())
def test_parse_qs_multiple_equal_signs(s):
    """Test parse_qs with multiple equal signs in value."""
    assume('&' not in s)
    assume('\x00' not in s)
    
    # Create a query string with equal signs in the value
    query = f"key={s}"
    parsed = urllib.parse.parse_qs(query)
    
    if s:
        assert 'key' in parsed
        assert parsed['key'][0] == s
    else:
        # Empty values are dropped by default
        assert 'key' not in parsed


@given(st.text(alphabet=st.characters(min_codepoint=128, max_codepoint=0x10ffff)))
def test_quote_non_ascii_characters(s):
    """Test quote with non-ASCII characters."""
    # Skip surrogates and other problematic characters
    assume(all('\ud800' > c or c > '\udfff' for c in s))
    assume(all(unicodedata.category(c)[0] != 'C' for c in s))
    
    quoted = urllib.parse.quote(s)
    
    # All non-ASCII should be percent-encoded
    for char in s:
        if ord(char) > 127:
            assert char not in quoted
    
    # Should be reversible
    unquoted = urllib.parse.unquote(quoted)
    assert s == unquoted


@given(st.dictionaries(
    st.text(min_size=1, alphabet=st.characters(blacklist_characters='&=\x00')),
    st.lists(st.text(alphabet=st.characters(blacklist_characters='&=\x00')), min_size=1, max_size=5),
    min_size=1,
    max_size=5
))
def test_urlencode_doseq_preserves_order(d):
    """Test that urlencode with doseq preserves list values."""
    encoded = urllib.parse.urlencode(d, doseq=True)
    decoded = urllib.parse.parse_qs(encoded)
    
    for key, values in d.items():
        assert key in decoded
        # parse_qs always returns lists
        decoded_values = decoded[key]
        
        # Check all original values are present (order may differ)
        for value in values:
            if value:  # Non-empty values
                assert value in decoded_values


@given(st.text())
def test_urlparse_invalid_port(s):
    """Test urlparse with invalid port numbers."""
    # Create URL with the given string as port
    url = f"http://example.com:{s}/path"
    
    try:
        parsed = urllib.parse.urlparse(url)
        # If parsing succeeds, accessing port should either return a valid int or None
        port = parsed.port
        if port is not None:
            assert isinstance(port, int)
            assert 0 <= port <= 65535
    except ValueError:
        # Invalid port should raise ValueError when accessed
        pass


@given(st.text(alphabet='0123456789abcdefABCDEF', min_size=2, max_size=2))
def test_unquote_valid_hex(hex_str):
    """Test unquote with valid hex sequences."""
    quoted = f"%{hex_str}"
    unquoted = urllib.parse.unquote(quoted)
    
    # Valid hex should be decoded
    expected_char = chr(int(hex_str, 16))
    assert unquoted == expected_char


@given(st.text())
def test_unquote_invalid_percent_encoding(s):
    """Test unquote with invalid percent encoding."""
    # Add invalid percent encoding
    if '%' not in s:
        invalid = s + '%ZZ'
        unquoted = urllib.parse.unquote(invalid)
        # Invalid percent encoding should be left as-is
        assert '%ZZ' in unquoted or unquoted == s + '%ZZ'


@given(st.text(min_size=1))
def test_quote_safe_parameter_validation(safe):
    """Test quote with various safe parameter values."""
    test_string = "test/string"
    
    # ASCII safe characters should work
    if all(ord(c) < 128 for c in safe):
        quoted = urllib.parse.quote(test_string, safe=safe)
        
        # Characters in safe should not be encoded
        for char in safe:
            if char in test_string:
                assert char in quoted or test_string.count(char) == 0
    else:
        # Non-ASCII in safe might cause issues
        try:
            quoted = urllib.parse.quote(test_string, safe=safe)
        except (UnicodeEncodeError, TypeError):
            pass  # Expected for non-ASCII safe characters


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])