#!/usr/bin/env python3
"""Investigate SplitMode behavior with invalid inputs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

from sudachipy import SplitMode
from sudachipy import errors

# Test cases based on documentation
test_cases = [
    # Valid cases from documentation
    ("A", "valid"),
    ("a", "valid"),
    ("B", "valid"),
    ("b", "valid"),
    ("C", "valid"),
    ("c", "valid"),
    (None, "valid - should default to C"),
    
    # Invalid cases
    ("0", "invalid"),
    ("D", "invalid"),
    ("abc", "invalid"),
    ("", "invalid - empty string"),
    ("1", "invalid"),
    ("X", "invalid"),
]

print("Testing SplitMode behavior:")
print("-" * 50)

for input_val, expected in test_cases:
    try:
        mode = SplitMode(input_val)
        print(f"✓ SplitMode({input_val!r}): Success - {mode}")
    except errors.SudachiError as e:
        print(f"✗ SplitMode({input_val!r}): SudachiError - {e}")
    except Exception as e:
        print(f"✗ SplitMode({input_val!r}): {type(e).__name__} - {e}")

print("\n" + "=" * 50)
print("Documentation vs Implementation Analysis:")
print("-" * 50)

# Check the docstring
print("SplitMode.__init__ docstring:")
print(SplitMode.__init__.__doc__)

print("\nObservations:")
print("1. The documentation says mode can be None (defaults to C)")
print("2. The documentation doesn't mention that invalid strings raise SudachiError")
print("3. This is a contract violation - the error behavior is not documented")