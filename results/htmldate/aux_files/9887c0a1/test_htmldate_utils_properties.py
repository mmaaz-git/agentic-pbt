"""
Property-based tests for htmldate.utils module using Hypothesis.
Testing fundamental properties that should always hold.
"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import hypothesis
import math

# Import the module we're testing
from htmldate.utils import (
    trim_text, 
    isutf8, 
    decode_file, 
    is_wrong_document,
    detect_encoding,
    repair_faulty_html,
    UNICODE_ALIASES
)
from htmldate.settings import MAX_FILE_SIZE


# Property 1: trim_text idempotence - applying twice should equal applying once
@given(st.text())
def test_trim_text_idempotence(text):
    """Test that trim_text is idempotent - f(f(x)) = f(x)"""
    result = trim_text(text)
    double_result = trim_text(result)
    assert result == double_result


# Property 2: trim_text normalizes any whitespace to single spaces
@given(st.text())
def test_trim_text_normalization(text):
    """Test that trim_text normalizes multiple spaces to single spaces"""
    result = trim_text(text)
    # After trimming, there should be no consecutive spaces
    assert "  " not in result
    # Result should not start or end with whitespace
    assert result == result.strip()


# Property 3: isutf8 correctness - should match Python's UTF-8 decoding
@given(st.binary())
def test_isutf8_correctness(data):
    """Test that isutf8 correctly identifies UTF-8 encoded bytes"""
    result = isutf8(data)
    
    # Check if Python can decode it as UTF-8
    try:
        data.decode('UTF-8')
        can_decode = True
    except UnicodeDecodeError:
        can_decode = False
    
    assert result == can_decode


# Property 4: decode_file round-trip - returns string input unchanged
@given(st.text())
def test_decode_file_string_passthrough(text):
    """Test that decode_file returns string input unchanged"""
    result = decode_file(text)
    assert result == text
    assert isinstance(result, str)


# Property 5: decode_file always returns a string
@given(st.binary(min_size=1, max_size=10000))
def test_decode_file_always_returns_string(data):
    """Test that decode_file always returns a string, even for arbitrary bytes"""
    result = decode_file(data)
    assert isinstance(result, str)
    assert len(result) > 0  # Should not return empty string for non-empty input


# Property 6: is_wrong_document invariants
@given(st.one_of(
    st.none(),
    st.just(""),
    st.just([]),
    st.binary(min_size=0, max_size=100),
    st.text(min_size=0, max_size=100)
))
def test_is_wrong_document_edge_cases(data):
    """Test is_wrong_document edge cases for empty/small data"""
    result = is_wrong_document(data)
    
    if data is None or not data:
        assert result is True, f"Expected True for empty/None data, got {result}"
    else:
        # Small non-empty data should be fine
        assert result is False, f"Expected False for small data, got {result}"
        

# Test large data separately
def test_is_wrong_document_large_data():
    """Test that is_wrong_document returns True for oversized data"""
    # Create data larger than MAX_FILE_SIZE
    large_data = "x" * (MAX_FILE_SIZE + 1)
    result = is_wrong_document(large_data)
    assert result is True, f"Expected True for oversized data (len={len(large_data)}), got {result}"
    
    # Also test with bytes
    large_bytes = b"x" * (MAX_FILE_SIZE + 1)
    result = is_wrong_document(large_bytes)
    assert result is True, f"Expected True for oversized bytes (len={len(large_bytes)}), got {result}"


# Property 7: is_wrong_document with valid data
@given(st.one_of(
    st.text(min_size=1, max_size=1000),
    st.binary(min_size=1, max_size=1000)
))
def test_is_wrong_document_valid_data(data):
    """Test that is_wrong_document returns False for valid small data"""
    result = is_wrong_document(data)
    assert result is False


# Property 8: detect_encoding and isutf8 consistency
@given(st.binary(min_size=1, max_size=10000))
def test_detect_encoding_utf8_consistency(data):
    """Test that detect_encoding is consistent with isutf8 for UTF-8 detection"""
    is_utf8 = isutf8(data)
    detected = detect_encoding(data)
    
    if is_utf8:
        # If isutf8 returns True, detect_encoding should return ["utf-8"]
        assert detected == ["utf-8"], f"Expected ['utf-8'] for UTF-8 data, got {detected}"
    else:
        # If isutf8 returns False, the result should not be just UTF-8 aliases
        if detected:
            # Check that it's not returning only UTF-8 aliases
            non_utf8 = [enc for enc in detected if enc not in UNICODE_ALIASES]
            # If there are results, at least one should not be a UTF-8 alias
            if len(detected) > 0:
                assert len(non_utf8) == len(detected), \
                    f"Non-UTF8 data returned UTF-8 aliases: {detected}"


# Property 9: repair_faulty_html idempotence
@given(st.text(min_size=0, max_size=1000))
def test_repair_faulty_html_idempotence(html_string):
    """Test that repair_faulty_html is idempotent"""
    # Extract beginning for the function
    beginning = html_string[:50].lower() if html_string else ""
    
    # Apply repair once
    repaired_once = repair_faulty_html(html_string, beginning)
    
    # Apply repair to the already repaired HTML
    beginning2 = repaired_once[:50].lower() if repaired_once else ""
    repaired_twice = repair_faulty_html(repaired_once, beginning2)
    
    assert repaired_once == repaired_twice


# Property 10: trim_text with added whitespace
@given(st.text(), st.text(alphabet=" \t\n\r"))
def test_trim_text_whitespace_invariant(text, whitespace):
    """Test that adding whitespace to already trimmed text doesn't change result"""
    trimmed = trim_text(text)
    # Add whitespace at the end
    with_whitespace = trimmed + whitespace
    trimmed_again = trim_text(with_whitespace)
    
    assert trimmed == trimmed_again


# Run with increased examples for better coverage
@settings(max_examples=500)
@given(st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"])))
def test_trim_text_preserves_content(text):
    """Test that trim_text preserves non-whitespace content"""
    # Remove all whitespace from original
    no_space_original = ''.join(text.split())
    
    # Trim and remove all whitespace
    trimmed = trim_text(text)
    no_space_trimmed = ''.join(trimmed.split())
    
    # The non-whitespace content should be preserved
    assert no_space_original == no_space_trimmed


if __name__ == "__main__":
    # Run the tests
    import pytest
    pytest.main([__file__, "-v"])