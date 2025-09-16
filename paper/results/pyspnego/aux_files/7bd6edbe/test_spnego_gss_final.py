#!/usr/bin/env python3
"""Final comprehensive tests for spnego.gss looking for any remaining bugs."""

import sys
import os
import random
import string

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import pytest

# Import the module to test
from spnego import _gss


# Test for extremely long inputs that might cause memory or performance issues
@given(st.integers(min_value=1000, max_value=5000))
@settings(max_examples=10)
def test_encode_kerb_password_large_input(size):
    """Test with larger (but not huge) inputs to check for performance issues."""
    # Create a string with mixed content
    parts = []
    for i in range(size):
        if i % 3 == 0:
            parts.append('\ud800')  # Surrogate
        elif i % 3 == 1:
            parts.append('a')  # ASCII
        else:
            parts.append('文')  # Non-ASCII UTF-8
    
    s = ''.join(parts)
    
    # This should complete without hanging or excessive memory use
    result = _gss._encode_kerb_password(s)
    
    # Verify the result is correct
    assert isinstance(result, bytes)
    # Can decode as UTF-8
    decoded = result.decode('utf-8')
    assert isinstance(decoded, str)


# Test all possible single-byte patterns through the function
def test_encode_kerb_password_all_single_chars():
    """Test encoding of all possible single characters in BMP."""
    failed_chars = []
    
    # Test a sample of all BMP characters
    for code in range(0, 0x10000, 0x100):  # Sample every 256th character
        if 0xd800 <= code <= 0xdfff:  # Skip surrogates
            continue
        
        try:
            char = chr(code)
            result = _gss._encode_kerb_password(char)
            
            # Should produce valid UTF-8
            decoded = result.decode('utf-8')
            
            # For non-surrogates, should match original
            assert decoded == char
            
        except Exception as e:
            failed_chars.append((code, str(e)))
    
    assert len(failed_chars) == 0, f"Failed characters: {failed_chars[:10]}"  # Show first 10 failures


# Test metamorphic property: f(x + y) = f(x) + f(y)
@given(st.text(max_size=100), st.text(max_size=100))
def test_encode_kerb_password_concatenation_property(x, y):
    """Concatenation property: encode(x + y) == encode(x) + encode(y)."""
    xy = x + y
    
    # Encode concatenated string
    encoded_xy = _gss._encode_kerb_password(xy)
    
    # Encode separately and concatenate
    encoded_x = _gss._encode_kerb_password(x)
    encoded_y = _gss._encode_kerb_password(y)
    encoded_x_plus_y = encoded_x + encoded_y
    
    assert encoded_xy == encoded_x_plus_y


# Test prefix/suffix property
@given(st.text(min_size=1, max_size=100))
def test_encode_kerb_password_prefix_suffix(s):
    """Adding a known prefix/suffix should result in predictable output."""
    prefix = "PREFIX"
    suffix = "SUFFIX"
    
    # Encode with prefix and suffix
    with_both = _gss._encode_kerb_password(prefix + s + suffix)
    
    # Should equal prefix encoding + s encoding + suffix encoding
    expected = _gss._encode_kerb_password(prefix) + _gss._encode_kerb_password(s) + _gss._encode_kerb_password(suffix)
    
    assert with_both == expected


# Test idempotence of replacement
def test_encode_kerb_password_idempotent_replacement():
    """Already-replaced surrogates (as U+FFFD) shouldn't be replaced again."""
    # Start with a surrogate
    original = '\ud800'
    
    # First encoding - surrogate becomes replacement char
    first_encoding = _gss._encode_kerb_password(original)
    assert first_encoding == b'\xef\xbf\xbd'
    
    # Decode back to get replacement character
    replacement_char = first_encoding.decode('utf-8')
    assert replacement_char == '\ufffd'
    
    # Encode again - should stay the same
    second_encoding = _gss._encode_kerb_password(replacement_char)
    assert second_encoding == b'\xef\xbf\xbd'
    
    # They should be equal
    assert first_encoding == second_encoding


# Test for any state leakage between calls
@given(st.lists(st.text(max_size=50), min_size=2, max_size=10))
def test_encode_kerb_password_no_state_leakage(strings):
    """Function should not maintain state between calls."""
    # Encode all strings twice in different orders
    first_pass = [_gss._encode_kerb_password(s) for s in strings]
    
    # Shuffle and encode again
    shuffled = strings.copy()
    random.shuffle(shuffled)
    
    # Create a mapping to compare
    results = {}
    for s in shuffled:
        results[s] = _gss._encode_kerb_password(s)
    
    # Results should be the same regardless of order
    for i, s in enumerate(strings):
        assert first_pass[i] == results[s]


# Test byte-by-byte building vs full string
@given(st.text(max_size=100))
def test_encode_kerb_password_byte_by_byte(s):
    """Building character by character should give same result as full string."""
    # Encode full string
    full_result = _gss._encode_kerb_password(s)
    
    # Encode character by character and concatenate
    parts = []
    for char in s:
        parts.append(_gss._encode_kerb_password(char))
    char_by_char = b''.join(parts)
    
    assert full_result == char_by_char


# Final stress test with random data
@given(st.binary(min_size=0, max_size=1000))
def test_encode_kerb_password_random_bytes_as_string(data):
    """Test with random bytes converted to string using surrogatepass."""
    try:
        # Try to decode as UTF-16 with surrogatepass (as mentioned in docstring)
        s = data.decode('utf-16-le', errors='surrogatepass')
    except:
        # If it fails (odd length, etc), skip this test case
        return
    
    # This should always work without raising
    result = _gss._encode_kerb_password(s)
    
    # Result should be valid UTF-8
    decoded = result.decode('utf-8')
    assert isinstance(decoded, str)


# Test the documented use case more thoroughly
def test_encode_kerb_password_utf16_le_roundtrip():
    """Test the specific UTF-16-LE use case from the docstring."""
    # Create various UTF-16-LE byte sequences
    test_cases = [
        b'\x00\xd8',  # High surrogate alone
        b'\x00\xdc',  # Low surrogate alone  
        b'\x00\xd8\x00\xdc',  # High + Low (would be valid pair)
        b'A\x00\x00\xd8B\x00',  # ASCII + surrogate + ASCII
        b'\x00\xd8\x00\xd8',  # Two high surrogates
        b'\x00\xdc\x00\xdc',  # Two low surrogates
    ]
    
    for utf16_bytes in test_cases:
        try:
            # Decode with surrogatepass as mentioned in docstring
            s = utf16_bytes.decode('utf-16-le', errors='surrogatepass')
            
            # Encode with our function
            result = _gss._encode_kerb_password(s)
            
            # Should produce valid UTF-8
            decoded = result.decode('utf-8')
            
            # All surrogates should be replaced
            for char in decoded:
                assert not (0xd800 <= ord(char) <= 0xdfff), f"Surrogate not replaced: U+{ord(char):04X}"
                
        except UnicodeDecodeError:
            # Some sequences might not be decodable even with surrogatepass
            pass


if __name__ == "__main__":
    # Run the tests
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"])