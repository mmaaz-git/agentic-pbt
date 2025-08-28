"""Minimal reproduction of the py_version validation bug."""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

from isort.settings import Config

# Test with newline character
try:
    config = Config(py_version="\n")
    print(f"Success: Created config with py_version='\\n'")
except ValueError as e:
    print(f"ValueError raised: {e}")
    print(f"Error message contains newline: {repr(str(e))}")

# Test with other whitespace characters
for test_char, name in [("\t", "tab"), (" ", "space"), ("\r", "carriage return")]:
    try:
        config = Config(py_version=test_char)
        print(f"Success: Created config with py_version={repr(test_char)} ({name})")
    except ValueError as e:
        print(f"ValueError for {name}: {repr(str(e)[:50])}...")

# Test that the error message format is problematic
print("\nThe issue: When py_version contains a newline, the error message includes it,")
print("which can make error messages harder to read and parse.")