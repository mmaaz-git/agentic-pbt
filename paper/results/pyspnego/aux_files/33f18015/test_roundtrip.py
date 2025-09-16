#!/usr/bin/env /root/hypothesis-llm/envs/pyspnego_env/bin/python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

import spnego._ntlm_raw.messages as messages
import spnego._ntlm_raw.crypto as crypto

print("Testing specific round-trip properties...")
print("=" * 60)

# Test 1: Check if Version handles overflow correctly
print("\nTest 1: Version overflow handling")
# These values are larger than their field sizes
large_major = 256  # Should wrap to 0 (8-bit field)
large_minor = 300  # Should wrap to 44 (8-bit field)
large_build = 70000  # Should wrap (16-bit field)
large_revision = 512  # Should wrap to 0 (8-bit field)

version = messages.Version(large_major, large_minor, large_build, large_revision)
print(f"  Input: major={large_major}, minor={large_minor}, build={large_build}, revision={large_revision}")
packed = version.pack()
unpacked = messages.Version.unpack(packed)
print(f"  After round-trip: major={unpacked.major}, minor={unpacked.minor}, build={unpacked.build}, revision={unpacked.revision}")
print(f"  Expected wrapping: major={large_major & 0xFF}, minor={large_minor & 0xFF}, build={large_build & 0xFFFF}, revision={large_revision & 0xFF}")

# Test 2: Empty TargetInfo behavior
print("\nTest 2: Empty TargetInfo")
empty_target = messages.TargetInfo([])
packed = empty_target.pack()
print(f"  Empty TargetInfo packed: {packed.hex()}")
print(f"  Length: {len(packed)} bytes")
unpacked = messages.TargetInfo.unpack(packed)
print(f"  Unpacked av_pairs count: {len(unpacked.av_pairs)}")

# Test 3: Negotiate with all flags set
print("\nTest 3: Negotiate with all flags")
all_flags = 0xFFFFFFFF
negotiate = messages.Negotiate(all_flags)
packed = negotiate.pack()
print(f"  All flags set: {hex(all_flags)}")
print(f"  Packed size: {len(packed)} bytes")
unpacked = messages.Negotiate.unpack(packed)
print(f"  Flags preserved: {unpacked.flags == all_flags}")

# Test 4: RC4 with repeated key
print("\nTest 4: RC4 state handling")
key = b"test"
data1 = b"Hello"
data2 = b"World"

# Test if RC4 handles state correctly
enc1 = crypto.rc4k(key, data1)
enc2 = crypto.rc4k(key, data2)
dec1 = crypto.rc4k(key, enc1)
dec2 = crypto.rc4k(key, enc2)

print(f"  Data1: {data1} -> Encrypted: {enc1.hex()} -> Decrypted: {dec1}")
print(f"  Data2: {data2} -> Encrypted: {enc2.hex()} -> Decrypted: {dec2}")
print(f"  Correctly decrypted: {dec1 == data1 and dec2 == data2}")

# Test 5: NTLM hash pattern detection edge cases
print("\nTest 5: NTLM hash pattern edge cases")
test_cases = [
    ("0123456789ABCDEF0123456789ABCDEF:FEDCBA9876543210FEDCBA9876543210", True),  # Valid uppercase
    ("0123456789abcdef0123456789abcdef:fedcba9876543210fedcba9876543210", True),  # Valid lowercase
    ("0123456789aBcDeF0123456789aBcDeF:fEdCbA9876543210fEdCbA9876543210", True),  # Valid mixed case
    ("0123456789ABCDEF0123456789ABCDE:FEDCBA9876543210FEDCBA9876543210", False),  # First part too short
    ("0123456789ABCDEF0123456789ABCDEF:FEDCBA9876543210FEDCBA987654321", False),  # Second part too short
    ("0123456789ABCDEF0123456789ABCDEFG:FEDCBA9876543210FEDCBA9876543210", False),  # First part too long
    ("0123456789ABCDEF0123456789ABCDEF:FEDCBA9876543210FEDCBA98765432100", False),  # Second part too long
    ("0123456789ABCDEF0123456789ABCDEF-FEDCBA9876543210FEDCBA9876543210", False),  # Wrong separator
    ("0123456789ABCDEF0123456789ABCDEF::FEDCBA9876543210FEDCBA9876543210", False),  # Double colon
    ("0123456789GHIJKL0123456789ABCDEF:FEDCBA9876543210FEDCBA9876543210", False),  # Invalid hex chars
]

for test_str, expected in test_cases:
    result = crypto.is_ntlm_hash(test_str)
    status = "✓" if result == expected else "✗"
    print(f"  {status} '{test_str[:40]}...' -> {result} (expected {expected})")

# Test 6: Password special cases
print("\nTest 6: Password hashing special cases")
special_passwords = [
    "",  # Empty password
    "a" * 14,  # Exactly 14 chars (LM limit)
    "a" * 15,  # Over 14 chars
    "密码",  # Chinese characters
    "пароль",  # Cyrillic
    "🔐",  # Emoji
    "\x00",  # Null byte
    "Pass\x00word",  # Embedded null
]

for pwd in special_passwords:
    try:
        lm_hash = crypto.lmowfv1(pwd)
        nt_hash = crypto.ntowfv1(pwd)
        display_pwd = repr(pwd) if len(repr(pwd)) < 30 else repr(pwd)[:27] + "..."
        print(f"  ✓ {display_pwd}: LM={lm_hash[:4].hex()}... ({len(lm_hash)} bytes), NT={nt_hash[:4].hex()}... ({len(nt_hash)} bytes)")
    except Exception as e:
        print(f"  ✗ {repr(pwd)}: Error - {e}")

print("\n" + "=" * 60)
print("Round-trip testing complete!")