import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

# Check splitlines behavior
from ast import _splitlines_no_ff as splitlines

# Test round-trip property
test_strings = [
    "hello\nworld",
    "single line",
    "",
    "\n",
    "line1\nline2\nline3",
    "trailing newline\n",
    "\nleading newline",
    "line with\r\nCRLF",
    "just\rCR",
]

print("Testing splitlines behavior:")
for s in test_strings:
    lines = splitlines(s)
    print(f"Input: {repr(s)}")
    print(f"Split: {lines}")
    # Try to reconstruct
    reconstructed = '\n'.join(lines)
    print(f"Reconstructed: {repr(reconstructed)}")
    print(f"Match: {s == reconstructed}")
    print()