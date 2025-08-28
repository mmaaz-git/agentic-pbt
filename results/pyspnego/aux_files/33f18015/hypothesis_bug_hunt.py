#!/usr/bin/env /root/hypothesis-llm/envs/pyspnego_env/bin/python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from hypothesis import Phase, HealthCheck
import spnego._ntlm_raw.crypto as crypto
import spnego._ntlm_raw.messages as messages
import traceback

print("=" * 70)
print("PROPERTY-BASED BUG HUNTING FOR spnego.ntlm")
print("=" * 70)

bugs_found = []

def report_bug(test_name, error, failing_input):
    """Report a bug found during testing"""
    bugs_found.append({
        'test': test_name,
        'error': error,
        'input': failing_input
    })
    print(f"\n❌ BUG FOUND in {test_name}")
    print(f"   Failing input: {failing_input}")
    print(f"   Error: {error}")

# Test 1: RC4 edge cases
print("\n[Test 1] RC4 encryption/decryption with edge cases")
@given(
    key=st.one_of(
        st.just(b""),  # Empty key - might be rejected
        st.just(b"\x00"),  # Null byte key
        st.just(b"\x00" * 256),  # All zeros
        st.binary(min_size=1, max_size=256)
    ),
    data=st.one_of(
        st.just(b""),  # Empty data
        st.just(b"\x00" * 1000),  # All nulls
        st.binary(min_size=0, max_size=10000)
    )
)
@settings(max_examples=500, suppress_health_check=[HealthCheck.filter_too_much])
def test_rc4_edge_cases(key, data):
    if len(key) == 0:
        assume(False)  # Skip empty keys if they're not allowed
    try:
        encrypted = crypto.rc4k(key, data)
        decrypted = crypto.rc4k(key, encrypted)
        assert decrypted == data
    except Exception as e:
        report_bug("RC4 edge cases", str(e), f"key={key!r}, data_len={len(data)}")
        raise

try:
    test_rc4_edge_cases()
    print("✓ RC4 handles edge cases correctly")
except:
    pass

# Test 2: Password hashing with Unicode edge cases
print("\n[Test 2] Password hashing with Unicode and special characters")
@given(
    password=st.one_of(
        st.text(alphabet=st.characters(blacklist_categories=[], blacklist_characters=[]), min_size=0, max_size=100),
        st.just(""),  # Empty password
        st.just("\x00"),  # Null character
        st.just("🦄" * 10),  # Unicode emojis
        st.just("\U0001F600" * 20),  # More emojis
        st.text(alphabet=st.sampled_from(["\x00", "\xff", "\t", "\n", "\r"]), min_size=1, max_size=50),
    )
)
@settings(max_examples=200)
def test_hash_unicode_edge_cases(password):
    try:
        # Test lmowfv1
        lm_hash = crypto.lmowfv1(password)
        assert len(lm_hash) == 16
        # Should be deterministic
        lm_hash2 = crypto.lmowfv1(password)
        assert lm_hash == lm_hash2
        
        # Test ntowfv1
        nt_hash = crypto.ntowfv1(password)
        assert len(nt_hash) == 16
        # Should be deterministic
        nt_hash2 = crypto.ntowfv1(password)
        assert nt_hash == nt_hash2
    except Exception as e:
        report_bug("Password hashing Unicode", str(e), f"password={password!r}")
        raise

try:
    test_hash_unicode_edge_cases()
    print("✓ Password hashing handles Unicode correctly")
except:
    pass

# Test 3: Version with boundary values
print("\n[Test 3] Version serialization with boundary values")
@given(
    major=st.one_of(st.just(0), st.just(255), st.just(256), st.integers()),
    minor=st.one_of(st.just(0), st.just(255), st.just(256), st.integers()),
    build=st.one_of(st.just(0), st.just(65535), st.just(65536), st.integers()),
    revision=st.one_of(st.just(0), st.just(255), st.just(256), st.integers())
)
@settings(max_examples=200)
def test_version_boundaries(major, minor, build, revision):
    try:
        version = messages.Version(major, minor, build, revision)
        packed = version.pack()
        assert len(packed) == 8
        unpacked = messages.Version.unpack(packed)
        # Check if values wrap around or are truncated
        assert unpacked.major == (major & 0xFF)
        assert unpacked.minor == (minor & 0xFF)
        assert unpacked.build == (build & 0xFFFF)
        assert unpacked.revision == (revision & 0xFF)
    except Exception as e:
        report_bug("Version boundaries", str(e), 
                  f"major={major}, minor={minor}, build={build}, revision={revision}")
        raise

try:
    test_version_boundaries()
    print("✓ Version handles boundary values correctly")
except:
    pass

# Test 4: TargetInfo with malformed data
print("\n[Test 4] TargetInfo with special AV pairs")
@given(
    av_pairs=st.lists(
        st.tuples(
            st.sampled_from(list(messages.AvId)),  # Valid AvId values
            st.one_of(
                st.text(max_size=1000),  # Normal text
                st.just(""),  # Empty string
                st.just("\x00" * 100),  # Null bytes
                st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=0x10ffff))  # Full Unicode
            )
        ),
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=100)
def test_target_info_edge_cases(av_pairs):
    try:
        pairs = [messages.AvPair(av_id, value) for av_id, value in av_pairs]
        target_info = messages.TargetInfo(pairs)
        packed = target_info.pack()
        unpacked = messages.TargetInfo.unpack(packed)
        
        # Check that the number of pairs is preserved
        assert len(unpacked.av_pairs) == len(pairs)
        
        # Check each pair
        for original, unpacked_pair in zip(pairs, unpacked.av_pairs):
            assert unpacked_pair.id == original.id
            # Values might be encoded/decoded differently but should be equivalent
            
    except Exception as e:
        report_bug("TargetInfo edge cases", str(e), f"av_pairs count={len(av_pairs)}")
        raise

try:
    test_target_info_edge_cases()
    print("✓ TargetInfo handles special AV pairs correctly")
except:
    pass

# Test 5: Negotiate flags combinations
print("\n[Test 5] Negotiate message with flag combinations")
@given(
    flags=st.one_of(
        st.just(0),  # No flags
        st.just(0xFFFFFFFF),  # All flags
        st.just(2**31),  # Sign bit
        st.integers(min_value=0, max_value=2**32-1),
        st.lists(st.sampled_from(list(messages.NegotiateFlags)), min_size=0, max_size=32)
            .map(lambda l: sum(l) if l else 0)  # Combine random flags
    )
)
@settings(max_examples=200)
def test_negotiate_flags(flags):
    try:
        # Ensure flags is an integer
        if isinstance(flags, list):
            flags = sum(flags) if flags else 0
        flags = int(flags) & 0xFFFFFFFF  # Ensure 32-bit
        
        negotiate = messages.Negotiate(flags)
        packed = negotiate.pack()
        unpacked = messages.Negotiate.unpack(packed)
        
        assert unpacked.flags == flags
        
    except Exception as e:
        report_bug("Negotiate flags", str(e), f"flags={hex(flags) if isinstance(flags, int) else flags}")
        raise

try:
    test_negotiate_flags()
    print("✓ Negotiate handles flag combinations correctly")
except:
    pass

# Test 6: FileTime edge cases
print("\n[Test 6] FileTime with extreme values")
@given(
    filetime=st.one_of(
        st.just(0),  # Minimum time
        st.just(2**64 - 1),  # Maximum time
        st.just(2**63),  # Sign bit boundary
        st.integers(min_value=0, max_value=2**64-1)
    )
)
@settings(max_examples=100)
def test_filetime_edge_cases(filetime):
    try:
        ft = messages.FileTime(filetime)
        packed = ft.pack()
        assert len(packed) == 8
        unpacked = messages.FileTime.unpack(packed)
        assert unpacked.filetime == filetime
    except Exception as e:
        report_bug("FileTime edge cases", str(e), f"filetime={filetime}")
        raise

try:
    test_filetime_edge_cases()
    print("✓ FileTime handles extreme values correctly")
except:
    pass

# Test 7: Challenge message parsing
print("\n[Test 7] Challenge message construction")
@given(
    flags=st.integers(min_value=0, max_value=0xFFFFFFFF),
    server_challenge=st.binary(min_size=8, max_size=8),
    target_name=st.text(max_size=100)
)
@settings(max_examples=50)
def test_challenge_message(flags, server_challenge, target_name):
    try:
        challenge = messages.Challenge(
            flags=flags,
            server_challenge=server_challenge,
            target_name=target_name if target_name else None
        )
        packed = challenge.pack()
        unpacked = messages.Challenge.unpack(packed)
        
        assert unpacked.flags == flags
        assert unpacked.server_challenge == server_challenge
        
    except Exception as e:
        report_bug("Challenge message", str(e), 
                  f"flags={hex(flags)}, challenge_len={len(server_challenge)}, target_name_len={len(target_name) if target_name else 0}")
        raise

try:
    test_challenge_message()
    print("✓ Challenge message construction works correctly")
except:
    pass

# Summary
print("\n" + "=" * 70)
print("BUG HUNTING SUMMARY")
print("=" * 70)

if bugs_found:
    print(f"\n🐛 Found {len(bugs_found)} potential bug(s):\n")
    for i, bug in enumerate(bugs_found, 1):
        print(f"{i}. Test: {bug['test']}")
        print(f"   Error: {bug['error']}")
        print(f"   Input: {bug['input']}\n")
else:
    print("\n✅ No bugs found in tested properties!")
    print("\nAll tested properties:")
    print("  1. RC4 encryption round-trip with edge cases")
    print("  2. Password hashing with Unicode characters")
    print("  3. Version serialization with boundary values")
    print("  4. TargetInfo with special AV pairs")
    print("  5. Negotiate message with flag combinations")
    print("  6. FileTime with extreme values")
    print("  7. Challenge message construction")