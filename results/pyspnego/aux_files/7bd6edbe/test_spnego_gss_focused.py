#!/usr/bin/env python3
"""Focused property-based tests for potential bugs in spnego.gss."""

import sys
import os

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume, example
import pytest

# Import the module to test
from spnego import _gss


# Deep dive into _encode_kerb_password edge cases
# Let's test with actual UTF-16 surrogate pair patterns

def test_encode_kerb_password_valid_surrogate_pair():
    """Valid surrogate pairs (if they were properly paired) should still be replaced."""
    # In UTF-16, valid surrogate pairs are:
    # High surrogate (0xD800-0xDBFF) followed by low surrogate (0xDC00-0xDFFF)
    # But in Python strings, lone surrogates are invalid
    
    # Test a technically "paired" surrogate (still invalid in UTF-8)
    high_surrogate = '\ud800'
    low_surrogate = '\udc00'
    
    # Even when "paired", these should be replaced
    result = _gss._encode_kerb_password(high_surrogate + low_surrogate)
    
    # Both should become replacement characters
    assert result == b'\xef\xbf\xbd\xef\xbf\xbd'


# Test boundary conditions for surrogates
def test_encode_kerb_password_surrogate_boundaries():
    """Test surrogate range boundaries."""
    # Just before surrogate range (U+D7FF)
    before_surrogate = '\ud7ff'
    result_before = _gss._encode_kerb_password(before_surrogate)
    # This is valid UTF-8
    assert result_before == before_surrogate.encode('utf-8')
    
    # First high surrogate (U+D800)
    first_high = '\ud800'
    result_first_high = _gss._encode_kerb_password(first_high)
    assert result_first_high == b'\xef\xbf\xbd'
    
    # Last high surrogate (U+DBFF)
    last_high = '\udbff'
    result_last_high = _gss._encode_kerb_password(last_high)
    assert result_last_high == b'\xef\xbf\xbd'
    
    # First low surrogate (U+DC00)
    first_low = '\udc00'
    result_first_low = _gss._encode_kerb_password(first_low)
    assert result_first_low == b'\xef\xbf\xbd'
    
    # Last low surrogate (U+DFFF)
    last_low = '\udfff'
    result_last_low = _gss._encode_kerb_password(last_low)
    assert result_last_low == b'\xef\xbf\xbd'
    
    # Just after surrogate range (U+E000)
    after_surrogate = '\ue000'
    result_after = _gss._encode_kerb_password(after_surrogate)
    # This is valid UTF-8
    assert result_after == after_surrogate.encode('utf-8')


# Test with real-world password patterns that might contain surrogates
def test_encode_kerb_password_machine_account_pattern():
    """Test pattern similar to machine/gMSA accounts that might have invalid UTF-16."""
    # Simulate a password that was incorrectly decoded from UTF-16
    # This might happen with randomly generated passwords
    password = 'ValidPrefix' + '\ud800' + 'ValidSuffix' + '\udc00'
    
    result = _gss._encode_kerb_password(password)
    expected = b'ValidPrefix\xef\xbf\xbdValidSuffix\xef\xbf\xbd'
    assert result == expected


# Test interaction with other Unicode edge cases
@given(st.sampled_from([
    '\x00',  # Null character
    '\ufffd',  # Replacement character itself
    '\ufffe',  # Noncharacter
    '\uffff',  # Noncharacter
]))
def test_encode_kerb_password_other_special_chars(char):
    """Test other special Unicode characters."""
    result = _gss._encode_kerb_password(char)
    # These should all encode normally (not replaced)
    expected = char.encode('utf-8')
    assert result == expected


# Test zero-width and combining characters
def test_encode_kerb_password_combining_chars():
    """Test with combining characters and zero-width chars."""
    # Combining acute accent after 'a'
    combining = 'a\u0301'  # á
    result = _gss._encode_kerb_password(combining)
    assert result == combining.encode('utf-8')
    
    # Zero-width joiner
    zwj = 'a\u200d'
    result_zwj = _gss._encode_kerb_password(zwj)
    assert result_zwj == zwj.encode('utf-8')


# Test maximum Unicode codepoint
def test_encode_kerb_password_max_codepoint():
    """Test with maximum valid Unicode codepoint."""
    # U+10FFFF is the maximum valid Unicode codepoint
    max_char = '\U0010ffff'
    result = _gss._encode_kerb_password(max_char)
    assert result == max_char.encode('utf-8')


# Performance/algorithmic complexity test
@given(st.integers(min_value=1, max_value=1000))
def test_encode_kerb_password_repeated_surrogates(n):
    """Test performance with many repeated surrogates."""
    # Create a string with n surrogates
    s = '\ud800' * n
    result = _gss._encode_kerb_password(s)
    
    # Each should become a 3-byte replacement
    assert len(result) == n * 3
    # All should be replacement chars
    assert result == b'\xef\xbf\xbd' * n


# Test interleaving patterns
@given(st.lists(
    st.sampled_from(['a', 'b', '\ud800', '\udc00', '1', '2']),
    min_size=0,
    max_size=100
))
def test_encode_kerb_password_interleaved_pattern(chars):
    """Test with interleaved valid and invalid characters."""
    s = ''.join(chars)
    result = _gss._encode_kerb_password(s)
    
    # Build expected result
    expected = b''
    for c in chars:
        if c in ['\ud800', '\udc00']:
            expected += b'\xef\xbf\xbd'
        else:
            expected += c.encode('utf-8')
    
    assert result == expected


# Test the concatenation behavior more thoroughly
@given(
    st.lists(st.text(max_size=10), min_size=0, max_size=10)
)
def test_encode_kerb_password_multi_concatenation(strings):
    """Encoding concatenated strings should equal concatenated encodings."""
    # Concatenate all strings first, then encode
    concat_then_encode = _gss._encode_kerb_password(''.join(strings))
    
    # Encode each string, then concatenate
    encode_then_concat = b''.join(_gss._encode_kerb_password(s) for s in strings)
    
    assert concat_then_encode == encode_then_concat


# Test empty strings in various positions
def test_encode_kerb_password_empty_string_positions():
    """Test empty strings don't affect encoding."""
    assert _gss._encode_kerb_password('') == b''
    assert _gss._encode_kerb_password('a' + '' + 'b') == b'ab'
    assert _gss._encode_kerb_password('' + '\ud800' + '') == b'\xef\xbf\xbd'


# Test specific case mentioned in docstring
def test_encode_kerb_password_docstring_example():
    """Test the specific use case mentioned in the docstring."""
    # The docstring mentions: b"...".decode("utf-16-le", errors="surrogatepass")
    # This preserves invalid surrogate pairs in the str value
    
    # Simulate a UTF-16-LE byte sequence with unpaired surrogates
    # High surrogate without low surrogate
    utf16_bytes = b'\x00\xd8'  # U+D800 in UTF-16-LE
    
    # Decode with surrogatepass to preserve the invalid surrogate
    s = utf16_bytes.decode('utf-16-le', errors='surrogatepass')
    assert s == '\ud800'
    
    # Now encode with our function
    result = _gss._encode_kerb_password(s)
    assert result == b'\xef\xbf\xbd'


if __name__ == "__main__":
    # Run the tests
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"])