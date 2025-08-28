#!/usr/bin/env /root/hypothesis-llm/envs/pyspnego_env/bin/python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

import spnego._ntlm_raw.crypto as crypto
import spnego._ntlm_raw.messages as messages
import struct

print("=" * 70)
print("FINAL ANALYSIS: Testing for potential bugs in spnego.ntlm")
print("=" * 70)

bugs_found = []

# Test 1: Version integer overflow behavior
print("\n[TEST 1] Version field overflow/truncation")
try:
    # Test values that exceed field sizes
    test_cases = [
        (256, 256, 65536, 256),  # All fields overflow
        (-1, -1, -1, -1),  # Negative values
        (1000000, 1000000, 1000000, 1000000),  # Very large values
    ]
    
    for major, minor, build, revision in test_cases:
        version = messages.Version(major, minor, build, revision)
        packed = version.pack()
        unpacked = messages.Version.unpack(packed)
        
        # Check if truncation happens as expected
        expected_major = major & 0xFF
        expected_minor = minor & 0xFF
        expected_build = build & 0xFFFF
        expected_revision = revision & 0xFF
        
        if (unpacked.major != expected_major or unpacked.minor != expected_minor or 
            unpacked.build != expected_build or unpacked.revision != expected_revision):
            print(f"  ❌ BUG: Version truncation incorrect")
            print(f"     Input: ({major}, {minor}, {build}, {revision})")
            print(f"     Expected: ({expected_major}, {expected_minor}, {expected_build}, {expected_revision})")
            print(f"     Got: ({unpacked.major}, {unpacked.minor}, {unpacked.build}, {unpacked.revision})")
            bugs_found.append("Version truncation")
        else:
            print(f"  ✓ Version correctly truncates: ({major}, {minor}, {build}, {revision}) -> ({unpacked.major}, {unpacked.minor}, {unpacked.build}, {unpacked.revision})")
            
except Exception as e:
    print(f"  ❌ ERROR in Version test: {e}")
    bugs_found.append(f"Version test error: {e}")

# Test 2: RC4 with edge case keys
print("\n[TEST 2] RC4 encryption with edge cases")
try:
    # Test empty key (should raise error)
    try:
        result = crypto.rc4k(b"", b"test")
        print(f"  ❌ BUG: RC4 accepts empty key (should reject)")
        bugs_found.append("RC4 accepts empty key")
    except Exception:
        print(f"  ✓ RC4 correctly rejects empty key")
    
    # Test very long key
    long_key = b"A" * 1000
    data = b"test data"
    encrypted = crypto.rc4k(long_key, data)
    decrypted = crypto.rc4k(long_key, encrypted)
    if decrypted != data:
        print(f"  ❌ BUG: RC4 fails with long key")
        bugs_found.append("RC4 long key failure")
    else:
        print(f"  ✓ RC4 handles long keys correctly")
        
except Exception as e:
    print(f"  ❌ ERROR in RC4 test: {e}")
    bugs_found.append(f"RC4 test error: {e}")

# Test 3: Password hashing with null bytes
print("\n[TEST 3] Password hashing with embedded nulls")
try:
    passwords_with_nulls = [
        "pass\x00word",  # Null in middle
        "\x00password",  # Null at start
        "password\x00",  # Null at end
    ]
    
    for pwd in passwords_with_nulls:
        lm_hash = crypto.lmowfv1(pwd)
        nt_hash = crypto.ntowfv1(pwd)
        
        # Check determinism
        lm_hash2 = crypto.lmowfv1(pwd)
        nt_hash2 = crypto.ntowfv1(pwd)
        
        if lm_hash != lm_hash2 or nt_hash != nt_hash2:
            print(f"  ❌ BUG: Hash not deterministic for password with null: {repr(pwd)}")
            bugs_found.append(f"Hash non-deterministic for: {repr(pwd)}")
        else:
            print(f"  ✓ Hashes are deterministic for: {repr(pwd)}")
            
except Exception as e:
    print(f"  ❌ ERROR in password hash test: {e}")
    bugs_found.append(f"Password hash test error: {e}")

# Test 4: FileTime boundary values
print("\n[TEST 4] FileTime with boundary values")
try:
    boundary_times = [
        0,  # Minimum
        2**64 - 1,  # Maximum unsigned 64-bit
        2**63,  # Sign bit flip point
        2**32,  # 32-bit boundary
    ]
    
    for ft_value in boundary_times:
        ft = messages.FileTime(ft_value)
        packed = ft.pack()
        unpacked = messages.FileTime.unpack(packed)
        
        if unpacked.filetime != ft_value:
            print(f"  ❌ BUG: FileTime round-trip failed for {ft_value}")
            print(f"     Got: {unpacked.filetime}")
            bugs_found.append(f"FileTime round-trip: {ft_value}")
        else:
            print(f"  ✓ FileTime round-trip OK for {ft_value}")
            
except Exception as e:
    print(f"  ❌ ERROR in FileTime test: {e}")
    bugs_found.append(f"FileTime test error: {e}")

# Test 5: TargetInfo with Unicode strings
print("\n[TEST 5] TargetInfo with Unicode domain names")
try:
    unicode_domains = [
        "тест.com",  # Cyrillic
        "测试.com",  # Chinese
        "🌍.com",  # Emoji
        "café.com",  # Accented characters
    ]
    
    for domain in unicode_domains:
        try:
            av_pair = messages.AvPair(messages.AvId.dns_domain_name, domain)
            target_info = messages.TargetInfo([av_pair])
            packed = target_info.pack()
            unpacked = messages.TargetInfo.unpack(packed)
            
            if len(unpacked.av_pairs) != 1:
                print(f"  ❌ BUG: TargetInfo lost AV pairs for domain: {domain}")
                bugs_found.append(f"TargetInfo Unicode: {domain}")
            else:
                unpacked_domain = unpacked.av_pairs[0].value
                if unpacked_domain != domain:
                    print(f"  ❌ BUG: TargetInfo Unicode mismatch")
                    print(f"     Original: {domain}")
                    print(f"     Unpacked: {unpacked_domain}")
                    bugs_found.append(f"TargetInfo Unicode mismatch: {domain}")
                else:
                    print(f"  ✓ TargetInfo handles Unicode: {domain}")
        except Exception as e:
            print(f"  ❌ ERROR handling Unicode domain {domain}: {e}")
            bugs_found.append(f"TargetInfo Unicode error: {domain}")
            
except Exception as e:
    print(f"  ❌ ERROR in TargetInfo test: {e}")
    bugs_found.append(f"TargetInfo test error: {e}")

# Test 6: Challenge message with invalid server challenge length
print("\n[TEST 6] Challenge message validation")
try:
    # Server challenge should be exactly 8 bytes
    invalid_challenges = [
        b"",  # Empty
        b"1234567",  # 7 bytes
        b"123456789",  # 9 bytes
    ]
    
    for challenge_bytes in invalid_challenges:
        try:
            challenge = messages.Challenge(
                flags=0,
                server_challenge=challenge_bytes
            )
            packed = challenge.pack()
            print(f"  ❌ BUG: Challenge accepts invalid length ({len(challenge_bytes)} bytes)")
            bugs_found.append(f"Challenge invalid length: {len(challenge_bytes)}")
        except Exception:
            print(f"  ✓ Challenge correctly rejects {len(challenge_bytes)}-byte challenge")
            
    # Test valid 8-byte challenge
    valid_challenge = b"12345678"
    challenge = messages.Challenge(flags=0, server_challenge=valid_challenge)
    packed = challenge.pack()
    unpacked = messages.Challenge.unpack(packed)
    if unpacked.server_challenge != valid_challenge:
        print(f"  ❌ BUG: Valid challenge not preserved")
        bugs_found.append("Challenge valid 8-byte failure")
    else:
        print(f"  ✓ Challenge handles valid 8-byte challenge")
        
except Exception as e:
    print(f"  ❌ ERROR in Challenge test: {e}")
    bugs_found.append(f"Challenge test error: {e}")

# Summary
print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)

if bugs_found:
    print(f"\n🐛 Found {len(bugs_found)} potential issue(s):")
    for i, bug in enumerate(bugs_found, 1):
        print(f"  {i}. {bug}")
    print("\nThese issues should be investigated further with actual execution.")
else:
    print("\n✅ No obvious bugs found based on static analysis!")
    print("\nAll tests passed:")
    print("  • Version field truncation works as expected")
    print("  • RC4 encryption/decryption is symmetric")
    print("  • Password hashing is deterministic")
    print("  • FileTime handles boundary values")
    print("  • TargetInfo handles Unicode")
    print("  • Challenge message validation")

print("\n" + "=" * 70)