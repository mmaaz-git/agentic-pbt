"""Analyze the null byte bug more carefully"""

import os
import testpath.commands as commands

# Check 1: Can we have null bytes in PATH normally?
try:
    os.environ['PATH'] = '/usr/bin\x00/usr/local/bin'
    print("OS allows null bytes in PATH")
except ValueError as e:
    print(f"OS does not allow null bytes in PATH: {e}")

# Check 2: What about other special characters?
original_path = os.environ.get('PATH', '')
test_chars = ['\n', '\t', '\r', ':', ';', ' ', '\\', '"', "'"]

for char in test_chars:
    try:
        test_dir = f"test{char}dir"
        commands.prepend_to_path(test_dir)
        print(f"prepend_to_path accepts {repr(char)}")
        commands.remove_from_path(test_dir)
    except Exception as e:
        print(f"prepend_to_path fails with {repr(char)}: {e}")

os.environ['PATH'] = original_path