#!/usr/bin/env python3
"""Property-based tests for spnego.gss module using Hypothesis."""

import sys
import os

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import pytest

# Import the module to test
from spnego import _gss


# Test 1: _encode_kerb_password handles invalid surrogates correctly
@given(st.text())
def test_encode_kerb_password_always_returns_bytes(s):
    """_encode_kerb_password should always return bytes, even with invalid surrogates."""
    result = _gss._encode_kerb_password(s)
    assert isinstance(result, bytes)


@given(st.text(alphabet=st.characters(blacklist_categories=('Cs',))))  # No surrogates
def test_encode_kerb_password_valid_utf8_round_trip(s):
    """Valid UTF-8 strings should encode correctly and be decodable."""
    encoded = _gss._encode_kerb_password(s)
    # The result should be valid UTF-8
    decoded = encoded.decode('utf-8')
    # For valid UTF-8, the result should match the input
    assert decoded == s


def test_encode_kerb_password_invalid_surrogate_replacement():
    """Invalid surrogates should be replaced with U+FFFD (replacement character)."""
    # Create a string with an invalid surrogate pair
    invalid_string = '\ud800'  # Lone high surrogate
    result = _gss._encode_kerb_password(invalid_string)
    # Should be replaced with UTF-8 encoding of U+FFFD
    assert result == b'\xef\xbf\xbd'
    
    # Another test with low surrogate
    invalid_string2 = '\udc00'  # Lone low surrogate  
    result2 = _gss._encode_kerb_password(invalid_string2)
    assert result2 == b'\xef\xbf\xbd'


@given(st.lists(st.one_of(
    st.text(min_size=1, max_size=10),
    st.just('\ud800'),  # Invalid high surrogate
    st.just('\udc00'),  # Invalid low surrogate
)))
def test_encode_kerb_password_mixed_valid_invalid(parts):
    """Mixed valid and invalid characters should be handled correctly."""
    s = ''.join(parts)
    result = _gss._encode_kerb_password(s)
    # Should always produce valid UTF-8 bytes
    assert isinstance(result, bytes)
    # Should be decodable as UTF-8 (invalid surrogates replaced)
    decoded = result.decode('utf-8')
    assert isinstance(decoded, str)


# Test 2: _gss_sasl_description caching behavior (idempotence)
class MockOID:
    """Mock OID object for testing."""
    def __init__(self, dotted_form):
        self.dotted_form = dotted_form


def test_gss_sasl_description_caching():
    """_gss_sasl_description should cache results (idempotence property)."""
    # Clear any existing cache
    if hasattr(_gss._gss_sasl_description, 'result'):
        delattr(_gss._gss_sasl_description, 'result')
    
    # Create a mock OID
    mock_oid = MockOID("1.2.3.4.5")
    
    # First call - will fail to get actual description but should cache None
    result1 = _gss._gss_sasl_description(mock_oid)
    
    # Second call - should return cached result
    result2 = _gss._gss_sasl_description(mock_oid)
    
    # Both results should be the same (caching/idempotence)
    assert result1 == result2
    
    # Verify the cache exists
    assert hasattr(_gss._gss_sasl_description, 'result')
    assert mock_oid.dotted_form in _gss._gss_sasl_description.result


# Test 3: Property testing for string encoding edge cases
@given(st.text())
@settings(max_examples=1000)
def test_encode_kerb_password_never_raises(s):
    """_encode_kerb_password should never raise an exception, regardless of input."""
    try:
        result = _gss._encode_kerb_password(s)
        assert isinstance(result, bytes)
    except Exception as e:
        pytest.fail(f"_encode_kerb_password raised exception: {e}")


# Test 4: Length relationship property
@given(st.text())
def test_encode_kerb_password_length_relationship(s):
    """The encoded length should be reasonable relative to input."""
    encoded = _gss._encode_kerb_password(s)
    # UTF-8 encoding can be at most 4 bytes per character
    # But since we replace surrogates with 3-byte sequence, max is 3 bytes per char
    assert len(encoded) <= len(s) * 4
    # Empty string should produce empty bytes
    if len(s) == 0:
        assert len(encoded) == 0


# Test 5: Specific documented behavior from docstring
def test_encode_kerb_password_documented_behavior():
    """Test the specific behavior documented in the function's docstring."""
    # The docstring mentions that invalid surrogate pairs in UTF-16 
    # should be preserved in the str value and replaced as needed
    
    # Test with a high surrogate followed by non-surrogate
    test_str = '\ud800X'
    result = _gss._encode_kerb_password(test_str)
    # High surrogate should be replaced, X should be normal
    expected = b'\xef\xbf\xbd' + b'X'
    assert result == expected
    
    # Test with multiple invalid surrogates
    test_str2 = '\ud800\udc00'  # Two invalid surrogates in sequence
    result2 = _gss._encode_kerb_password(test_str2)
    # Both should be replaced
    expected2 = b'\xef\xbf\xbd\xef\xbf\xbd'
    assert result2 == expected2


if __name__ == "__main__":
    # Run the tests
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"])