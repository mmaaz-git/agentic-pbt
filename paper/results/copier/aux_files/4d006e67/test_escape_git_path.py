"""Test escape_git_path for potential bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._tools import escape_git_path

# Test with the same problematic characters
test_cases = [
    '0\x80',  # The character that breaks normalize_git_path
    'test\x81test',
    '\x90\x91\x92',
    'valid\xfftext',
    '\\backslash',
    'trailing ',
    ' leading',
    '\ttab\t',
]

print("Testing escape_git_path with various inputs:")
for input_str in test_cases:
    try:
        result = escape_git_path(input_str)
        print(f"✓ {repr(input_str)} -> {repr(result)}")
    except Exception as e:
        print(f"✗ {repr(input_str)} -> {type(e).__name__}: {e}")