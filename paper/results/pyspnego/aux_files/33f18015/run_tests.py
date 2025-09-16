#!/usr/bin/env /root/hypothesis-llm/envs/pyspnego_env/bin/python3

import os
import sys
import traceback

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, Verbosity
import spnego._ntlm_raw.crypto as crypto
import spnego._ntlm_raw.messages as messages

print("Starting property-based testing of spnego.ntlm module...")
print("=" * 60)

test_results = []

def run_test(test_func, test_name):
    """Run a single property test and report results"""
    print(f"\nRunning: {test_name}")
    try:
        # Run the test with explicit settings
        test_with_settings = settings(
            max_examples=100,
            verbosity=Verbosity.verbose,
            print_blob=True
        )(test_func)
        test_with_settings()
        print(f"✓ PASSED")
        test_results.append((test_name, "PASSED", None))
    except Exception as e:
        print(f"✗ FAILED: {e}")
        test_results.append((test_name, "FAILED", str(e)))
        traceback.print_exc()
        return False
    return True


# Test 1: RC4 round-trip
@given(key=st.binary(min_size=1, max_size=256), data=st.binary(min_size=0, max_size=1000))
def test_rc4_round_trip(key, data):
    encrypted = crypto.rc4k(key, data)
    decrypted = crypto.rc4k(key, encrypted)
    assert decrypted == data

run_test(test_rc4_round_trip, "RC4 round-trip property")


# Test 2: lmowfv1 determinism
@given(password=st.text(min_size=0, max_size=50))
def test_lmowfv1_deterministic(password):
    hash1 = crypto.lmowfv1(password)
    hash2 = crypto.lmowfv1(password)
    assert hash1 == hash2

run_test(test_lmowfv1_deterministic, "lmowfv1 determinism")


# Test 3: lmowfv1 output size
@given(password=st.text(min_size=0, max_size=50))
def test_lmowfv1_size(password):
    hash_result = crypto.lmowfv1(password)
    assert len(hash_result) == 16

run_test(test_lmowfv1_size, "lmowfv1 output size")


# Test 4: ntowfv1 determinism
@given(password=st.text(min_size=0, max_size=50))
def test_ntowfv1_deterministic(password):
    hash1 = crypto.ntowfv1(password)
    hash2 = crypto.ntowfv1(password)
    assert hash1 == hash2

run_test(test_ntowfv1_deterministic, "ntowfv1 determinism")


# Test 5: ntowfv1 output size
@given(password=st.text(min_size=0, max_size=50))
def test_ntowfv1_size(password):
    hash_result = crypto.ntowfv1(password)
    assert len(hash_result) == 16

run_test(test_ntowfv1_size, "ntowfv1 output size")


# Test 6: is_ntlm_hash with valid format
@given(hash_string=st.from_regex(r'^[a-fA-F0-9]{32}:[a-fA-F0-9]{32}$', fullmatch=True))
def test_is_ntlm_hash_valid(hash_string):
    assert crypto.is_ntlm_hash(hash_string)

run_test(test_is_ntlm_hash_valid, "is_ntlm_hash recognizes valid format")


# Test 7: is_ntlm_hash rejects invalid format
@given(hash_string=st.text(max_size=100).filter(lambda s: ':' not in s or s.count(':') > 1))
def test_is_ntlm_hash_invalid(hash_string):
    # Should reject strings without exactly one colon
    assert not crypto.is_ntlm_hash(hash_string)

run_test(test_is_ntlm_hash_invalid, "is_ntlm_hash rejects invalid format")


# Test 8: Version round-trip
@given(
    major=st.integers(min_value=0, max_value=255),
    minor=st.integers(min_value=0, max_value=255),
    build=st.integers(min_value=0, max_value=65535),
    revision=st.integers(min_value=0, max_value=255)
)
def test_version_round_trip(major, minor, build, revision):
    version = messages.Version(major, minor, build, revision)
    packed = version.pack()
    assert len(packed) == 8
    unpacked = messages.Version.unpack(packed)
    assert unpacked.major == version.major
    assert unpacked.minor == version.minor
    assert unpacked.build == version.build
    assert unpacked.revision == version.revision

run_test(test_version_round_trip, "Version pack/unpack round-trip")


# Test 9: FileTime round-trip
@given(filetime=st.integers(min_value=0, max_value=2**64-1))
def test_filetime_round_trip(filetime):
    ft = messages.FileTime(filetime)
    packed = ft.pack()
    assert len(packed) == 8
    unpacked = messages.FileTime.unpack(packed)
    assert unpacked.filetime == ft.filetime

run_test(test_filetime_round_trip, "FileTime pack/unpack round-trip")


# Test 10: Negotiate message round-trip
@given(flags=st.integers(min_value=0, max_value=0xFFFFFFFF))
def test_negotiate_round_trip(flags):
    negotiate = messages.Negotiate(flags)
    packed = negotiate.pack()
    unpacked = messages.Negotiate.unpack(packed)
    assert unpacked.flags == negotiate.flags

run_test(test_negotiate_round_trip, "Negotiate message round-trip")


# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

passed = sum(1 for _, status, _ in test_results if status == "PASSED")
failed = sum(1 for _, status, _ in test_results if status == "FAILED")

print(f"Tests run: {len(test_results)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")

if failed > 0:
    print("\nFailed tests:")
    for name, status, error in test_results:
        if status == "FAILED":
            print(f"  - {name}")
            if error:
                print(f"    Error: {error[:200]}")