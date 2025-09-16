import re
import sys

sys.path.insert(0, '/root/hypothesis-llm/envs/pytest-pretty_env/lib/python3.13/site-packages')
import pytest_pretty

# The regex pattern from pytest_pretty
print("ANSI escape regex pattern:")
print(repr(pytest_pretty.ansi_escape.pattern))
print()

# Test cases for ANSI escape removal
test_cases = [
    '\x1b',                          # Lone ESC character
    '\x1b[',                         # ESC followed by [
    '\x1b[31m',                      # Red color code
    '\x1b[0m',                       # Reset code
    'Hello\x1bWorld',                # ESC in middle of text
    '\x1b[1;31mRed Bold\x1b[0m',    # Full ANSI sequence
    '\x1b@',                         # ESC followed by @
    '\x1bM',                         # ESC followed by M
    '\x80',                          # High control character
    '\x9f',                          # Another high control character
]

print("Testing ANSI escape removal:")
print("-" * 60)
for test in test_cases:
    cleaned = pytest_pretty.ansi_escape.sub('', test)
    has_esc = '\x1b' in cleaned
    print(f"Input:   {repr(test)}")
    print(f"Output:  {repr(cleaned)}")
    print(f"ESC removed: {'No' if has_esc else 'Yes'}")
    print()

# Let's understand what the regex is supposed to match
print("Understanding the regex pattern:")
print("Pattern: r'(?:\\x1B[@-_]|[\\x80-\\x9F])[0-?]*[ -/]*[@-~]'")
print()
print("This matches:")
print("1. Either:")
print("   a. ESC (\\x1B) followed by [@-_] (chars 64-95)")
print("   b. OR chars [\\x80-\\x9F] (high control chars)")
print("2. Followed by zero or more [0-?] (chars 48-63)")
print("3. Followed by zero or more [ -/] (chars 32-47)")
print("4. Followed by one char from [@-~] (chars 64-126)")
print()
print("Problem: A lone '\\x1b' doesn't match because it needs at least")
print("         one more character from [@-_] or needs to be followed")
print("         by the full sequence ending with [@-~]")