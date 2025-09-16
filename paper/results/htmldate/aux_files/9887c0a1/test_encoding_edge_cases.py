"""
Focused property-based tests for encoding detection in htmldate.utils.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, seed, HealthCheck
import codecs

from htmldate.utils import detect_encoding, decode_file, isutf8, UNICODE_ALIASES


# Generate bytes that are definitely not UTF-8
def not_utf8_bytes():
    """Strategy for bytes that are definitely not valid UTF-8"""
    return st.binary(min_size=1, max_size=100).filter(lambda b: not isutf8(b))


# Test detect_encoding with various encodings
@given(st.text(min_size=1, max_size=100))
def test_detect_encoding_with_encoded_text(text):
    """Test detect_encoding with text encoded in various formats"""
    # Try different encodings
    for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
        try:
            encoded = text.encode(encoding)
            result = detect_encoding(encoded)
            
            # If it's valid UTF-8, result should be ["utf-8"]
            if isutf8(encoded):
                assert result == ["utf-8"]
            else:
                # Otherwise, result should not contain only UTF-8 aliases
                if result:
                    # Filter out UTF-8 aliases
                    non_utf8 = [e for e in result if e not in UNICODE_ALIASES]
                    # If the bytes are not UTF-8, we shouldn't get empty list
                    # (since detect_encoding filters out UTF-8 aliases)
                    assert len(non_utf8) == len(result)
        except UnicodeEncodeError:
            # Some text can't be encoded in certain encodings
            pass


# Test detect_encoding returns consistent results
@given(st.binary(min_size=1, max_size=1000))
def test_detect_encoding_consistency(data):
    """Test that detect_encoding returns consistent results for same input"""
    result1 = detect_encoding(data)
    result2 = detect_encoding(data)
    
    # Should return same result for same input
    assert result1 == result2


# Test decode_file with various problematic byte sequences
@given(not_utf8_bytes())
def test_decode_file_non_utf8_bytes(data):
    """Test decode_file with bytes that are definitely not UTF-8"""
    result = decode_file(data)
    
    # Should always return a string
    assert isinstance(result, str)
    
    # Should not be empty for non-empty input
    assert len(result) > 0


# Test decode_file with mixed valid/invalid UTF-8
@given(st.binary(min_size=1, max_size=50), st.binary(min_size=1, max_size=50))
def test_decode_file_mixed_bytes(valid_part, invalid_part):
    """Test decode_file with mixed valid and invalid byte sequences"""
    # Create valid UTF-8 bytes
    valid_utf8 = "Hello".encode('utf-8')
    
    # Mix valid UTF-8 with random bytes
    mixed = valid_utf8 + invalid_part + valid_part
    
    result = decode_file(mixed)
    
    # Should always return a string
    assert isinstance(result, str)


# Test edge case: bytes that look like UTF-8 BOM
def test_detect_encoding_with_bom():
    """Test detect_encoding with UTF-8 BOM"""
    # UTF-8 BOM
    bom_utf8 = b'\xef\xbb\xbf' + "Hello".encode('utf-8')
    result = detect_encoding(bom_utf8)
    
    # Should detect as UTF-8
    assert result == ["utf-8"]


# Test with invalid UTF-8 sequences
@given(st.sampled_from([
    b'\x80',  # Invalid start byte
    b'\xc0\x80',  # Overlong encoding
    b'\xed\xa0\x80',  # UTF-16 surrogate
    b'\xf5\x80\x80\x80',  # Out of range
    b'\xc2',  # Incomplete sequence
    b'\xe0\x80\x80',  # Invalid continuation
]))
def test_detect_encoding_invalid_utf8(invalid_bytes):
    """Test detect_encoding with known invalid UTF-8 sequences"""
    result = detect_encoding(invalid_bytes)
    
    # Should not return only UTF-8 since these are invalid
    assert result != ["utf-8"]
    
    # Should return some encoding guesses (might be empty after filtering)
    assert isinstance(result, list)


# Test empty input
def test_detect_encoding_empty():
    """Test detect_encoding with empty bytes"""
    result = detect_encoding(b"")
    
    # Empty bytes are technically valid UTF-8
    assert result == ["utf-8"]


# Test large input without Hypothesis (to test the chunking in detect_encoding)
def test_detect_encoding_large_input():
    """Test detect_encoding with large input (tests chunking logic at 15000 byte boundary)"""
    # Create a large UTF-8 string
    large_utf8 = ("Hello World! " * 1500).encode('utf-8')  # ~19500 bytes
    result = detect_encoding(large_utf8)
    assert result == ["utf-8"]
    
    # Create large non-UTF-8 bytes  
    large_latin1 = ("Héllo Wörld! " * 1500).encode('latin-1')
    result = detect_encoding(large_latin1)
    # Should not be UTF-8
    assert result != ["utf-8"]
    assert isinstance(result, list)


# Test decode_file preserves valid Unicode 
@given(st.text(alphabet=st.characters(min_codepoint=0x100, max_codepoint=0x10000, 
                                     blacklist_categories=["Cs"])))  # Exclude surrogates
def test_decode_file_preserves_unicode(text):
    """Test that decode_file preserves Unicode characters correctly"""
    # Encode as UTF-8
    encoded = text.encode('utf-8')
    
    # Decode
    result = decode_file(encoded)
    
    # Should preserve the original text
    assert result == text


# Test that detect_encoding handles all zero bytes
def test_detect_encoding_null_bytes():
    """Test detect_encoding with null bytes"""
    null_bytes = b'\x00' * 100
    result = detect_encoding(null_bytes)
    
    # Null bytes are valid UTF-8
    assert result == ["utf-8"]


# Test interaction between detect_encoding and decode_file
@given(st.binary(min_size=1, max_size=500))
def test_encoding_detection_roundtrip(data):
    """Test that decode_file can handle any encoding detect_encoding returns"""
    encodings = detect_encoding(data)
    
    # decode_file should be able to handle the data
    result = decode_file(data)
    
    # Should always succeed in returning a string
    assert isinstance(result, str)
    
    # If detect_encoding returned encodings, decode_file should have succeeded
    if encodings:
        assert len(result) > 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])