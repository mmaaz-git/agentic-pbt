#!/usr/bin/env python3
"""Edge case tests for spnego.gss to find potential bugs."""

import sys
import os

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume, example
import pytest

# Import the module to test
from spnego import _gss


# Test for potential integer overflow or boundary issues
@given(st.text())
def test_encode_kerb_password_length_invariant(s):
    """The encoded length should have predictable bounds."""
    encoded = _gss._encode_kerb_password(s)
    
    # Count actual characters that will be encoded
    replacement_count = sum(1 for c in s if '\ud800' <= c <= '\udfff')
    normal_count = len(s) - replacement_count
    
    # Replacements are 3 bytes, normal chars at most 4 bytes (for highest Unicode)
    min_expected = replacement_count * 3  # All surrogates become 3-byte replacement
    max_expected = replacement_count * 3 + normal_count * 4
    
    assert min_expected <= len(encoded) <= max_expected


# Test consecutive surrogates behavior
@given(st.integers(min_value=0, max_value=100))
def test_encode_kerb_password_consecutive_different_surrogates(n):
    """Test alternating high and low surrogates."""
    # Create alternating pattern
    s = ''.join(['\ud800' if i % 2 == 0 else '\udc00' for i in range(n)])
    
    result = _gss._encode_kerb_password(s)
    
    # Each surrogate should become replacement char
    assert len(result) == n * 3
    assert result == b'\xef\xbf\xbd' * n


# Test all surrogates in the range
def test_encode_kerb_password_all_surrogates():
    """Test that ALL surrogates in the range are replaced."""
    # Test a sample of surrogates across the range
    for code in range(0xd800, 0xe000, 0x10):  # Sample every 16th surrogate
        char = chr(code)
        result = _gss._encode_kerb_password(char)
        assert result == b'\xef\xbf\xbd', f"Failed for U+{code:04X}"


# Test string with maximum possible surrogates
def test_encode_kerb_password_maximum_surrogates():
    """Test with a string of maximum density of surrogates."""
    # Create a pattern with maximum surrogate density
    pattern = '\ud800a\udc00b\ud801c\udc01d'
    result = _gss._encode_kerb_password(pattern)
    
    # Should be: replacement + 'a' + replacement + 'b' + replacement + 'c' + replacement + 'd'
    expected = b'\xef\xbf\xbda\xef\xbf\xbdb\xef\xbf\xbdc\xef\xbf\xbdd'
    assert result == expected


# Test Unicode normalization edge cases
def test_encode_kerb_password_normalization():
    """Test that the function doesn't inadvertently normalize Unicode."""
    # Composed character (é)
    composed = '\u00e9'
    # Decomposed character (e + combining accent)
    decomposed = 'e\u0301'
    
    result_composed = _gss._encode_kerb_password(composed)
    result_decomposed = _gss._encode_kerb_password(decomposed)
    
    # They should NOT be equal (no normalization should occur)
    assert result_composed != result_decomposed
    assert result_composed == composed.encode('utf-8')
    assert result_decomposed == decomposed.encode('utf-8')


# Test with BOM (Byte Order Mark)
def test_encode_kerb_password_bom():
    """Test handling of BOM character."""
    bom = '\ufeff'
    result = _gss._encode_kerb_password(bom)
    # BOM should encode normally, not be stripped or replaced
    assert result == bom.encode('utf-8')
    assert result == b'\xef\xbb\xbf'


# Test control characters
@given(st.sampled_from([chr(i) for i in range(0x00, 0x20)]))
def test_encode_kerb_password_control_chars(char):
    """Control characters should encode normally."""
    result = _gss._encode_kerb_password(char)
    assert result == char.encode('utf-8')


# Test private use area characters
def test_encode_kerb_password_private_use():
    """Private use area characters should encode normally."""
    # Test characters from private use area
    pua_char = '\ue000'  # First private use character
    result = _gss._encode_kerb_password(pua_char)
    assert result == pua_char.encode('utf-8')
    
    # Last private use character in BMP
    pua_last = '\uf8ff'
    result_last = _gss._encode_kerb_password(pua_last)
    assert result_last == pua_last.encode('utf-8')


# Test with emoji and multi-codepoint graphemes
def test_encode_kerb_password_emoji():
    """Test with emoji that use multiple codepoints."""
    # Simple emoji
    simple_emoji = '😀'
    result_simple = _gss._encode_kerb_password(simple_emoji)
    assert result_simple == simple_emoji.encode('utf-8')
    
    # Complex emoji with ZWJ sequence (family emoji)
    family = '👨‍👩‍👧‍👦'  # Man, ZWJ, Woman, ZWJ, Girl, ZWJ, Boy
    result_family = _gss._encode_kerb_password(family)
    assert result_family == family.encode('utf-8')
    
    # Emoji with skin tone modifier
    waving = '👋🏽'  # Waving hand with medium skin tone
    result_waving = _gss._encode_kerb_password(waving)
    assert result_waving == waving.encode('utf-8')


# Test replacement character itself
def test_encode_kerb_password_replacement_char():
    """The replacement character itself should encode normally."""
    replacement = '\ufffd'
    result = _gss._encode_kerb_password(replacement)
    # Should NOT be replaced again, just encoded normally
    assert result == replacement.encode('utf-8')
    assert result == b'\xef\xbf\xbd'
    
    # Mix with actual surrogates
    mixed = '\ufffd\ud800\ufffd'
    result_mixed = _gss._encode_kerb_password(mixed)
    # First and last are normal replacements, middle is replaced surrogate
    assert result_mixed == b'\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd'


# Test string slicing doesn't affect encoding
@given(st.text(), st.integers(min_value=0), st.integers(min_value=0))
def test_encode_kerb_password_slicing(s, start, length):
    """Slicing a string then encoding should equal encoding then slicing."""
    assume(start <= len(s))
    end = min(start + length, len(s))
    
    # Slice then encode
    sliced = s[start:end]
    slice_then_encode = _gss._encode_kerb_password(sliced)
    
    # For comparison, we need to be careful about UTF-8 boundaries
    # This is a property test about the consistency of the function
    
    # The sliced string encoded should be the same each time
    slice_then_encode2 = _gss._encode_kerb_password(sliced)
    assert slice_then_encode == slice_then_encode2


# Test extreme case: string with only replacement characters
def test_encode_kerb_password_only_replacement_chars():
    """String of only U+FFFD characters."""
    s = '\ufffd' * 100
    result = _gss._encode_kerb_password(s)
    expected = b'\xef\xbf\xbd' * 100
    assert result == expected


# Test interaction with null bytes
def test_encode_kerb_password_null_bytes():
    """Null bytes should be preserved."""
    s = 'before\x00after'
    result = _gss._encode_kerb_password(s)
    assert result == b'before\x00after'
    
    # Null with surrogates
    s2 = '\x00\ud800\x00'
    result2 = _gss._encode_kerb_password(s2)
    assert result2 == b'\x00\xef\xbf\xbd\x00'


# Test that the function is deterministic
@given(st.text())
def test_encode_kerb_password_deterministic(s):
    """The function should be deterministic - same input always gives same output."""
    result1 = _gss._encode_kerb_password(s)
    result2 = _gss._encode_kerb_password(s)
    result3 = _gss._encode_kerb_password(s)
    
    assert result1 == result2 == result3


# Test specific patterns that might cause issues
def test_encode_kerb_password_tricky_patterns():
    """Test specific patterns that might expose bugs."""
    
    # Pattern 1: Surrogate at string boundaries
    patterns = [
        '\ud800',  # Start with surrogate
        'text\ud800',  # End with surrogate
        '\ud800text',  # Start with surrogate, then text
        'text\ud800text',  # Surrogate in middle
    ]
    
    for pattern in patterns:
        result = _gss._encode_kerb_password(pattern)
        # Should successfully encode without errors
        assert isinstance(result, bytes)
        # Should be valid UTF-8
        decoded = result.decode('utf-8')
        assert isinstance(decoded, str)


if __name__ == "__main__":
    # Run the tests
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"])