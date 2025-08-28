"""Minimal reproduction of the normalize_git_path bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._tools import normalize_git_path

# The minimal failing case found by Hypothesis
path = '\x80'
quoted_path = f'"{path}"'

print(f"Input path: {repr(path)}")
print(f"Quoted path: {repr(quoted_path)}")

try:
    result = normalize_git_path(quoted_path)
    print(f"Result: {repr(result)}")
except UnicodeDecodeError as e:
    print(f"Error: {e}")
    print("\nThis is a bug - normalize_git_path should handle non-UTF-8 sequences gracefully")

# Let's also test with other non-UTF-8 bytes
print("\n--- Testing other non-UTF-8 sequences ---")
for byte_val in [0x80, 0xFF, 0xC0, 0xC1]:
    test_path = chr(byte_val)
    quoted = f'"{test_path}"'
    try:
        result = normalize_git_path(quoted)
        print(f"byte {hex(byte_val)}: SUCCESS - {repr(result)}")
    except Exception as e:
        print(f"byte {hex(byte_val)}: FAILED - {type(e).__name__}: {e}")