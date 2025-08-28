"""Reproduce the decode_docs bug."""

import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')
import yq

# Test case 1: Two zeros concatenated without separator
print("Test 1: Two zeros without separator")
json_str = json.dumps(0) + json.dumps(0)  # Results in "00"
print(f"JSON string: {repr(json_str)}")

decoder = json.JSONDecoder()
try:
    decoded = list(yq.decode_docs(json_str, decoder))
    print(f"Decoded: {decoded}")
    print(f"Expected: [0, 0]")
    print(f"Match: {decoded == [0, 0]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50 + "\n")

# Test case 2: Two different numbers without separator
print("Test 2: 0 and -1 without separator")
json_str = json.dumps(0) + json.dumps(-1)  # Results in "0-1"
print(f"JSON string: {repr(json_str)}")

try:
    decoded = list(yq.decode_docs(json_str, decoder))
    print(f"Decoded: {decoded}")
    print(f"Expected: [0, -1]")
    print(f"Match: {decoded == [0, -1]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50 + "\n")

# Test case 3: With proper separator (how it's expected to work)
print("Test 3: With newline separator (expected usage)")
json_str = json.dumps(0) + "\n" + json.dumps(-1)
print(f"JSON string: {repr(json_str)}")

try:
    decoded = list(yq.decode_docs(json_str, decoder))
    print(f"Decoded: {decoded}")
    print(f"Expected: [0, -1]")
    print(f"Match: {decoded == [0, -1]}")
except Exception as e:
    print(f"Error: {e}")