import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

# Test strip behavior
test_cases = [
    "  \n  def foo():\n    pass\n  ",
    "\n\n\ndef foo():\n    pass",
    "def foo():\n    pass",
    "   ",
    "",
    "\n",
    "  \t  \n  ",
]

for code in test_cases:
    stripped = code.strip()
    double_stripped = stripped.strip()
    print(f"Original: {repr(code)}")
    print(f"Stripped: {repr(stripped)}")
    print(f"Idempotent: {stripped == double_stripped}")
    print()