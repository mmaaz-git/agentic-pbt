#!/usr/bin/env /root/hypothesis-llm/envs/pyspnego_env/bin/python3

import os
import sys

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import spnego._ntlm_raw.crypto as crypto
import spnego._ntlm_raw.messages as messages


# Strategy for generating valid keys and data for RC4
rc4_key_strategy = st.binary(min_size=1, max_size=256)
rc4_data_strategy = st.binary(min_size=0, max_size=10000)

@given(key=rc4_key_strategy, data=rc4_data_strategy)
def test_rc4_round_trip(key, data):
    """Test that RC4 encryption is its own inverse: rc4k(k, rc4k(k, data)) == data"""
    encrypted = crypto.rc4k(key, data)
    decrypted = crypto.rc4k(key, encrypted)
    assert decrypted == data, f"RC4 round-trip failed: original != decrypted"


# Strategy for generating passwords
password_strategy = st.text(min_size=0, max_size=100)

@given(password=password_strategy)
def test_lmowfv1_deterministic(password):
    """Test that lmowfv1 is deterministic - same password always produces same hash"""
    hash1 = crypto.lmowfv1(password)
    hash2 = crypto.lmowfv1(password)
    assert hash1 == hash2, f"lmowfv1 not deterministic for password: {password!r}"


@given(password=password_strategy)
def test_lmowfv1_output_size(password):
    """Test that lmowfv1 always produces 16-byte output"""
    hash_result = crypto.lmowfv1(password)
    assert len(hash_result) == 16, f"lmowfv1 output size is {len(hash_result)}, expected 16"


@given(password=password_strategy)
def test_ntowfv1_deterministic(password):
    """Test that ntowfv1 is deterministic - same password always produces same hash"""
    hash1 = crypto.ntowfv1(password)
    hash2 = crypto.ntowfv1(password)
    assert hash1 == hash2, f"ntowfv1 not deterministic for password: {password!r}"


@given(password=password_strategy)
def test_ntowfv1_output_size(password):
    """Test that ntowfv1 always produces 16-byte output"""
    hash_result = crypto.ntowfv1(password)
    assert len(hash_result) == 16, f"ntowfv1 output size is {len(hash_result)}, expected 16"


# Strategy for valid NTLM hash format
valid_ntlm_hash = st.from_regex(r'^[a-fA-F0-9]{32}:[a-fA-F0-9]{32}$', fullmatch=True)

@given(hash_string=valid_ntlm_hash)
def test_is_ntlm_hash_valid(hash_string):
    """Test that is_ntlm_hash correctly identifies valid NTLM hash strings"""
    assert crypto.is_ntlm_hash(hash_string), f"is_ntlm_hash failed to recognize valid hash: {hash_string}"


# Strategy for invalid NTLM hash formats
invalid_ntlm_hash = st.one_of(
    st.text(max_size=100).filter(lambda s: ':' not in s),  # No colon
    st.text(max_size=100).filter(lambda s: s.count(':') > 1),  # Too many colons
    st.from_regex(r'^[a-fA-F0-9]{1,31}:[a-fA-F0-9]{32}$'),  # First part too short
    st.from_regex(r'^[a-fA-F0-9]{32}:[a-fA-F0-9]{1,31}$'),  # Second part too short
    st.from_regex(r'^[g-zG-Z]+:[a-fA-F0-9]{32}$'),  # Invalid hex chars
)

@given(hash_string=invalid_ntlm_hash)
def test_is_ntlm_hash_invalid(hash_string):
    """Test that is_ntlm_hash correctly rejects invalid NTLM hash strings"""
    assert not crypto.is_ntlm_hash(hash_string), f"is_ntlm_hash incorrectly accepted invalid hash: {hash_string}"


# Test NTLM message round-trip for Negotiate message
@given(flags=st.integers(min_value=0, max_value=0xFFFFFFFF))
@settings(max_examples=50)
def test_negotiate_message_round_trip(flags):
    """Test that Negotiate message can be packed and unpacked correctly"""
    # Create a Negotiate message
    negotiate = messages.Negotiate(flags)
    
    # Pack it to bytes
    packed = negotiate.pack()
    
    # Unpack it back
    unpacked = messages.Negotiate.unpack(packed)
    
    # Check that flags are preserved
    assert unpacked.flags == negotiate.flags, f"Negotiate round-trip failed: flags {negotiate.flags} != {unpacked.flags}"


# Test Version round-trip property
@given(
    major=st.integers(min_value=0, max_value=255),
    minor=st.integers(min_value=0, max_value=255),
    build=st.integers(min_value=0, max_value=65535),
    revision=st.integers(min_value=0, max_value=255)
)
def test_version_round_trip(major, minor, build, revision):
    """Test that Version can be packed and unpacked correctly"""
    version = messages.Version(major, minor, build, revision)
    packed = version.pack()
    
    # Version.pack() returns exactly 8 bytes
    assert len(packed) == 8, f"Version.pack() returned {len(packed)} bytes, expected 8"
    
    unpacked = messages.Version.unpack(packed)
    assert unpacked.major == version.major
    assert unpacked.minor == version.minor
    assert unpacked.build == version.build
    assert unpacked.revision == version.revision


# Test FileTime round-trip  
@given(filetime=st.integers(min_value=0, max_value=2**64-1))
def test_filetime_round_trip(filetime):
    """Test that FileTime can be packed and unpacked correctly"""
    ft = messages.FileTime(filetime)
    packed = ft.pack()
    
    # FileTime.pack() returns exactly 8 bytes
    assert len(packed) == 8, f"FileTime.pack() returned {len(packed)} bytes, expected 8"
    
    unpacked = messages.FileTime.unpack(packed)
    assert unpacked.filetime == ft.filetime


if __name__ == "__main__":
    # Run all tests
    import pytest
    pytest.main([__file__, "-v"])