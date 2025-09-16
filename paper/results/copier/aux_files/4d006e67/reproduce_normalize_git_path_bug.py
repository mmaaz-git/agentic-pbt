"""Reproduce the normalize_git_path Unicode bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._tools import normalize_git_path

# Test the minimal failing case from Hypothesis
test_input = '"0\x80"'  # A quoted path with byte 0x80
print(f"Testing normalize_git_path with input: {repr(test_input)}")

try:
    result = normalize_git_path(test_input)
    print(f"Result: {repr(result)}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    
# Let's understand what's happening step by step
print("\nStep-by-step analysis:")
path = test_input

# Step 1: Remove surrounding quotes  
if path[0] == path[-1] == '"':
    path = path[1:-1]
print(f"After removing quotes: {repr(path)}")

# Step 2: Repair double-quotes (not applicable here)
path = path.replace('\\"', '"')
print(f"After repairing double-quotes: {repr(path)}")

# Step 3: Unescape escape characters
print(f"Encoding to latin-1 with backslashreplace...")
encoded = path.encode("latin-1", "backslashreplace")
print(f"Encoded: {encoded}")

print(f"Decoding from unicode-escape...")
decoded = encoded.decode("unicode-escape")
print(f"Decoded: {repr(decoded)}")

# Step 4: Convert octal to utf8 - THIS IS WHERE IT FAILS
print(f"Re-encoding to latin-1...")
reencoded = decoded.encode("latin-1", "backslashreplace")
print(f"Re-encoded: {reencoded}")

print(f"Attempting to decode as utf-8...")
try:
    final = reencoded.decode("utf-8")
    print(f"Final: {repr(final)}")
except UnicodeDecodeError as e:
    print(f"ERROR: {e}")
    print(f"The byte sequence {reencoded} is not valid UTF-8")