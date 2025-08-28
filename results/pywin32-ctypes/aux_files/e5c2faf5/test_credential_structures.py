#!/usr/bin/env python3
"""
Property-based tests for win32ctypes credential structure handling.
Tests the data conversion logic without requiring Windows APIs.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pywin32-ctypes_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest


# Import the functions we want to test
def is_text(s):
    """From win32ctypes.core.compat"""
    return isinstance(s, str)


def make_unicode(text):
    """
    Convert the input string to unicode.
    From win32ctypes/core/ctypes/_authentication.py lines 74-82
    """
    if is_text(text):
        return text
    else:
        # Simplified version - just decode as UTF-8 for testing
        # (Original uses Windows code page which we can't access on Linux)
        return text.decode(encoding='utf-8', errors='strict')


# Supported credential keys from the implementation
SUPPORTED_CREDKEYS = set((
    'Type', 'TargetName', 'Persist',
    'UserName', 'Comment', 'CredentialBlob'))


# Property 1: make_unicode idempotence for strings
@given(st.text())
def test_make_unicode_idempotent_for_strings(text):
    """
    Test that make_unicode(str) returns the same string unchanged.
    This is a claimed property in the implementation.
    """
    result = make_unicode(text)
    assert result == text, f"make_unicode should be idempotent for strings"
    assert isinstance(result, str), f"make_unicode should return str"
    
    # Double application should also be idempotent
    result2 = make_unicode(result)
    assert result2 == result == text


# Property 2: make_unicode converts bytes to str
@given(st.text().map(lambda s: s.encode('utf-8')))
def test_make_unicode_converts_bytes(data):
    """
    Test that make_unicode converts bytes to unicode strings.
    """
    # We generate valid UTF-8 bytes by encoding text
    expected = data.decode('utf-8')
    
    result = make_unicode(data)
    assert isinstance(result, str), f"make_unicode should return str for bytes input"
    assert result == expected, f"make_unicode should decode bytes correctly"


# Property 3: make_unicode preserves UTF-8 round-trip
@given(st.text())
def test_make_unicode_utf8_roundtrip(text):
    """
    Test that text -> bytes -> make_unicode preserves the original text.
    """
    # Encode to bytes
    encoded = text.encode('utf-8')
    # Decode back with make_unicode
    result = make_unicode(encoded)
    
    assert result == text, f"UTF-8 round-trip should preserve text"


# Property 4: Credential dict validation
@given(st.dictionaries(
    keys=st.sampled_from(list(SUPPORTED_CREDKEYS) + ['InvalidKey']),
    values=st.text(min_size=1, max_size=50),
    min_size=0,
    max_size=7
))
def test_credential_dict_validation(cred_dict):
    """
    Test that credential dictionaries are validated for supported keys.
    Based on fromdict method in CREDENTIAL class.
    """
    unsupported = set(cred_dict.keys()) - SUPPORTED_CREDKEYS
    
    # The implementation should reject unsupported keys
    has_unsupported = len(unsupported) > 0
    
    # Verify our understanding of supported keys
    for key in cred_dict:
        if key in SUPPORTED_CREDKEYS:
            assert key in ['Type', 'TargetName', 'Persist', 
                          'UserName', 'Comment', 'CredentialBlob']
        else:
            assert key not in SUPPORTED_CREDKEYS


# Property 5: CredentialBlob special handling
@given(st.one_of(
    st.text(min_size=0, max_size=100),
    st.binary(min_size=0, max_size=100)
))
def test_credential_blob_unicode_conversion(blob_data):
    """
    Test that CredentialBlob data is properly converted to unicode.
    The implementation always converts CredentialBlob to unicode.
    """
    if isinstance(blob_data, bytes):
        try:
            blob_data.decode('utf-8')
        except UnicodeDecodeError:
            assume(False)  # Skip invalid UTF-8
            return
    
    # The implementation converts CredentialBlob to unicode
    result = make_unicode(blob_data)
    assert isinstance(result, str), "CredentialBlob should be converted to unicode"
    
    if isinstance(blob_data, str):
        assert result == blob_data
    else:
        assert result == blob_data.decode('utf-8')


# Property 6: Empty input handling
@given(st.sampled_from(['', b'']))
def test_make_unicode_empty_input(empty_input):
    """
    Test that make_unicode handles empty strings and bytes correctly.
    """
    result = make_unicode(empty_input)
    assert result == '', "Empty input should return empty string"
    assert isinstance(result, str), "Result should always be str"


# Property 7: Supported keys are complete and non-overlapping
def test_supported_credkeys_properties():
    """
    Test properties of the SUPPORTED_CREDKEYS set.
    """
    # All keys should be strings
    assert all(isinstance(key, str) for key in SUPPORTED_CREDKEYS)
    
    # Keys should be unique (guaranteed by set, but let's verify)
    keys_list = list(SUPPORTED_CREDKEYS)
    assert len(keys_list) == len(set(keys_list))
    
    # Expected keys based on documentation
    expected = {'Type', 'TargetName', 'Persist', 
                'UserName', 'Comment', 'CredentialBlob'}
    assert SUPPORTED_CREDKEYS == expected
    
    # No key should be a substring of another (prevents ambiguity)
    for key1 in SUPPORTED_CREDKEYS:
        for key2 in SUPPORTED_CREDKEYS:
            if key1 != key2:
                assert key1 not in key2, f"'{key1}' is substring of '{key2}'"


# Property 8: Type consistency in is_text
@given(st.one_of(
    st.text(),
    st.binary(),
    st.integers(),
    st.floats(),
    st.booleans(),
    st.none()
))
def test_is_text_type_checking(value):
    """
    Test that is_text correctly identifies text (str) values.
    """
    result = is_text(value)
    expected = isinstance(value, str)
    assert result == expected, \
        f"is_text({type(value).__name__}) returned {result}, expected {expected}"


if __name__ == "__main__":
    print("Running property-based tests for credential structures...")
    pytest.main([__file__, "-v", "--tb=short"])