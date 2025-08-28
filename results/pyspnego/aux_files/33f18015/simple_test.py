#!/usr/bin/env /root/hypothesis-llm/envs/pyspnego_env/bin/python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

import spnego._ntlm_raw.crypto as crypto

# Test 1: RC4 round-trip with simple case
print("Test 1: RC4 round-trip")
key = b"test_key"
data = b"Hello, World!"
encrypted = crypto.rc4k(key, data)
decrypted = crypto.rc4k(key, encrypted)
print(f"  Original:  {data}")
print(f"  Encrypted: {encrypted}")
print(f"  Decrypted: {decrypted}")
print(f"  Success: {data == decrypted}")

# Test 2: Hash determinism
print("\nTest 2: lmowfv1 determinism")
password = "TestPassword123"
hash1 = crypto.lmowfv1(password)
hash2 = crypto.lmowfv1(password)
print(f"  Hash1: {hash1.hex()}")
print(f"  Hash2: {hash2.hex()}")
print(f"  Same: {hash1 == hash2}")
print(f"  Length: {len(hash1)}")

# Test 3: ntowfv1 determinism
print("\nTest 3: ntowfv1 determinism")
hash1 = crypto.ntowfv1(password)
hash2 = crypto.ntowfv1(password)
print(f"  Hash1: {hash1.hex()}")
print(f"  Hash2: {hash2.hex()}")
print(f"  Same: {hash1 == hash2}")
print(f"  Length: {len(hash1)}")

# Test 4: is_ntlm_hash
print("\nTest 4: is_ntlm_hash predicate")
valid = "0123456789abcdef0123456789abcdef:fedcba9876543210fedcba9876543210"
invalid = "not_a_hash"
print(f"  Valid hash format: {valid}")
print(f"  is_ntlm_hash(valid): {crypto.is_ntlm_hash(valid)}")
print(f"  Invalid format: {invalid}")
print(f"  is_ntlm_hash(invalid): {crypto.is_ntlm_hash(invalid)}")