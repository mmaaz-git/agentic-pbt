#!/usr/bin/env python3
"""Extended property-based tests for spnego.gss module using Hypothesis."""

import sys
import os

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume, example
import pytest

# Import the module to test
from spnego import _gss
from spnego.iov import BufferType, IOVBuffer, IOVResBuffer


# Test for _create_iov_result function
class MockGSSIOVBuffer:
    """Mock GSSAPI IOV Buffer for testing."""
    def __init__(self, buffer_type, value):
        self.type = buffer_type
        self.value = value


class MockGSSIOV:
    """Mock GSSAPI IOV container."""
    def __init__(self, buffers):
        self.buffers = buffers
    
    def __iter__(self):
        return iter(self.buffers)


@given(st.lists(
    st.tuples(
        st.integers(min_value=0, max_value=10),  # buffer type
        st.binary(min_size=0, max_size=100)  # buffer data
    ),
    min_size=0,
    max_size=10
))
def test_create_iov_result_preserves_data(buffer_list):
    """_create_iov_result should preserve buffer type and data."""
    # Create mock IOV buffers
    mock_buffers = [MockGSSIOVBuffer(bt, data) for bt, data in buffer_list]
    mock_iov = MockGSSIOV(mock_buffers)
    
    # Convert using the function
    result = _gss._create_iov_result(mock_iov)
    
    # Verify the result
    assert isinstance(result, tuple)
    assert len(result) == len(buffer_list)
    
    for i, (orig_type, orig_data) in enumerate(buffer_list):
        res_buffer = result[i]
        assert isinstance(res_buffer, IOVResBuffer)
        assert res_buffer.type.value == orig_type
        assert res_buffer.data == orig_data


# Test empty IOV
def test_create_iov_result_empty():
    """_create_iov_result should handle empty IOV correctly."""
    mock_iov = MockGSSIOV([])
    result = _gss._create_iov_result(mock_iov)
    assert result == ()


# Test None values in IOV buffers
@given(st.lists(
    st.tuples(
        st.integers(min_value=0, max_value=10),
        st.one_of(st.none(), st.binary(max_size=50))
    ),
    min_size=1,
    max_size=5
))
def test_create_iov_result_handles_none(buffer_list):
    """_create_iov_result should handle None values in buffers."""
    mock_buffers = [MockGSSIOVBuffer(bt, data) for bt, data in buffer_list]
    mock_iov = MockGSSIOV(mock_buffers)
    
    result = _gss._create_iov_result(mock_iov)
    
    assert len(result) == len(buffer_list)
    for i, (orig_type, orig_data) in enumerate(buffer_list):
        assert result[i].type.value == orig_type
        assert result[i].data == orig_data


# Test for very large buffer types (edge case)
@given(st.integers())
def test_create_iov_result_large_buffer_types(buffer_type):
    """_create_iov_result should handle any integer buffer type."""
    mock_buffer = MockGSSIOVBuffer(buffer_type, b"test")
    mock_iov = MockGSSIOV([mock_buffer])
    
    try:
        result = _gss._create_iov_result(mock_iov)
        # BufferType constructor might raise if value is invalid
        assert len(result) == 1
        assert result[0].data == b"test"
    except (ValueError, OverflowError):
        # BufferType may only accept certain values
        pass


# More aggressive testing of _encode_kerb_password
@given(st.text())
@settings(max_examples=5000)
def test_encode_kerb_password_output_is_valid_utf8(s):
    """Output of _encode_kerb_password should always be valid UTF-8."""
    encoded = _gss._encode_kerb_password(s)
    # This should never raise
    decoded = encoded.decode('utf-8')
    assert isinstance(decoded, str)


# Test concatenation property
@given(st.text(), st.text())
def test_encode_kerb_password_concatenation(s1, s2):
    """Encoding concatenated strings should equal concatenated encodings."""
    concat_then_encode = _gss._encode_kerb_password(s1 + s2)
    encode_then_concat = _gss._encode_kerb_password(s1) + _gss._encode_kerb_password(s2)
    assert concat_then_encode == encode_then_concat


# Test with strings containing only surrogates
@given(st.lists(st.sampled_from(['\ud800', '\ud801', '\udc00', '\udc01']), min_size=1, max_size=10))
def test_encode_kerb_password_only_surrogates(surrogate_list):
    """Strings with only invalid surrogates should all become replacement chars."""
    s = ''.join(surrogate_list)
    encoded = _gss._encode_kerb_password(s)
    # Each surrogate should become the 3-byte replacement character
    expected_length = len(surrogate_list) * 3
    assert len(encoded) == expected_length
    # All should be replacement characters
    decoded = encoded.decode('utf-8')
    assert all(c == '\ufffd' for c in decoded)


# Test interaction between normal chars and surrogates
@given(
    st.text(alphabet=st.characters(blacklist_categories=('Cs',)), min_size=1, max_size=5),
    st.sampled_from(['\ud800', '\udc00']),
    st.text(alphabet=st.characters(blacklist_categories=('Cs',)), min_size=1, max_size=5)
)
def test_encode_kerb_password_mixed_content(prefix, surrogate, suffix):
    """Test encoding with normal text, surrogate, then normal text."""
    combined = prefix + surrogate + suffix
    encoded = _gss._encode_kerb_password(combined)
    
    # Should be: encoded(prefix) + replacement_char + encoded(suffix)
    expected = _gss._encode_kerb_password(prefix) + b'\xef\xbf\xbd' + _gss._encode_kerb_password(suffix)
    assert encoded == expected


# Edge case: empty string
def test_encode_kerb_password_empty_string():
    """Empty string should produce empty bytes."""
    assert _gss._encode_kerb_password("") == b""


# Test with very long strings
@given(st.text(min_size=10000, max_size=10001))
@settings(max_examples=10)
def test_encode_kerb_password_long_strings(s):
    """Should handle very long strings without issues."""
    encoded = _gss._encode_kerb_password(s)
    assert isinstance(encoded, bytes)
    # Should be valid UTF-8
    decoded = encoded.decode('utf-8')
    assert isinstance(decoded, str)


if __name__ == "__main__":
    # Run the tests
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"])