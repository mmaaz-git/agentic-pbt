#!/usr/bin/env python3
import argcomplete
from argcomplete import split_line

# Test the failing case found by hypothesis
print("Testing split_line with unclosed quote and point beyond string length...")
line = '"'
point = 2

try:
    result = split_line(line, point)
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# More tests with unclosed quotes
print("\nTesting other unclosed quote scenarios...")
test_cases = [
    ('"', None),
    ("'", None),
    ('"hello', None),
    ("'world", None),
    ('"', 0),
    ('"', 1),
    ('"', 2),
    ('"', 10),
]

for line, point in test_cases:
    try:
        result = split_line(line, point)
        print(f"split_line({line!r}, {point}) = {result}")
    except Exception as e:
        print(f"split_line({line!r}, {point}) raised {type(e).__name__}: {e}")