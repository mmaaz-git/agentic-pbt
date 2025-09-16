"""Reproduce the hash_key length issue."""

import sys
from base64 import b64encode
from hashlib import sha224
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')
from yq.loader import hash_key

# Test with empty string
print("Testing hash_key with empty string:")
result = hash_key("")
print(f"Hash result: {repr(result)}")
print(f"Hash length: {len(result)}")

# Manual calculation to verify
manual_hash = b64encode(sha224("".encode()).digest()).decode()
print(f"Manual calculation: {repr(manual_hash)}")
print(f"Manual length: {len(manual_hash)}")
print(f"Match: {result == manual_hash}")

print("\n" + "="*50 + "\n")

# Test with various inputs to see the pattern
test_inputs = ["", "a", "test", "longer string", b"binary"]
for inp in test_inputs:
    result = hash_key(inp)
    print(f"Input: {repr(inp)[:20]}, Hash length: {len(result)}")