"""Test more cases to understand the normalize_git_path bug better."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._tools import normalize_git_path

# Test cases that should work (based on the documentation)
good_cases = [
    (r'"\303\242\303\261"', 'âñ'),  # The example from the docstring
    (r'"\tfoo\\b\nar"', '\tfoo\b\nar'),  # Another example from docstring
    ('normal_file.txt', 'normal_file.txt'),  # Normal filename
]

print("Testing documented examples:")
for input_str, expected in good_cases:
    try:
        result = normalize_git_path(input_str)
        print(f"✓ {repr(input_str)} -> {repr(result)} (expected: {repr(expected)})")
        if result != expected:
            print(f"  WARNING: Result doesn't match expected!")
    except Exception as e:
        print(f"✗ {repr(input_str)} -> ERROR: {e}")

# Test problematic cases found by Hypothesis
print("\nTesting problematic cases:")
bad_cases = [
    '"0\x80"',  # The minimal failing case
    '"test\x81test"',  # Another invalid UTF-8 byte
    '"\x90\x91\x92"',  # Multiple invalid UTF-8 bytes
    '"valid\xfftext"',  # 0xFF is valid Latin-1 but not UTF-8
]

for input_str in bad_cases:
    try:
        result = normalize_git_path(input_str)
        print(f"✓ {repr(input_str)} -> {repr(result)}")
    except UnicodeDecodeError as e:
        print(f"✗ {repr(input_str)} -> UnicodeDecodeError: {e}")

# Test edge cases
print("\nTesting edge cases:")
edge_cases = [
    '""',  # Empty quoted string
    '"',   # Single quote
    'no_quotes',  # No quotes at all
]

for input_str in edge_cases:
    try:
        result = normalize_git_path(input_str)
        print(f"✓ {repr(input_str)} -> {repr(result)}")
    except Exception as e:
        print(f"✗ {repr(input_str)} -> {type(e).__name__}: {e}")