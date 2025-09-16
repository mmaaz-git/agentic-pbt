#!/usr/bin/env python3
"""Test a refined fix for the whitespace bug."""

import sys
import ast
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import parser

def DefaultParseValue_Fixed(value):
    """Fixed version that tries stripping whitespace if initial parse fails."""
    # First, try parsing as-is (for backwards compatibility)
    try:
        return parser._LiteralEval(value)
    except (SyntaxError, ValueError):
        # If that fails, try stripping whitespace and parsing again
        stripped = value.strip()
        if stripped != value:  # Only try again if we actually stripped something
            try:
                return parser._LiteralEval(stripped)
            except (SyntaxError, ValueError):
                pass
        # If all parsing attempts fail, return original value
        return value

# Test the refined fix
print("Testing the refined fix:")
print("-" * 60)

test_cases = [
    # These should parse to their values
    ('42', 42),
    (' 42', 42),
    ('  42  ', 42),
    ('True', True),
    (' True ', True),
    ('[1, 2, 3]', [1, 2, 3]),
    (' [1, 2, 3] ', [1, 2, 3]),
    ('{"a": 1}', {'a': 1}),
    (' {"a": 1} ', {'a': 1}),
    ('"hello"', 'hello'),
    (' "hello" ', 'hello'),
    ('None', None),
    (' None ', None),
    
    # These should remain as strings (can't be parsed)
    ('not_a_literal', 'not_a_literal'),
    ('  spaces_preserved  ', '  spaces_preserved  '),  # Unparseable, keep spaces
    ('1 + 1', '1 + 1'),  # Binary operation
    (' 1 + 1 ', ' 1 + 1 '),  # Binary op with spaces
]

all_pass = True
for input_val, expected in test_cases:
    result = DefaultParseValue_Fixed(input_val)
    
    if result == expected:
        status = "✓"
    else:
        status = "✗"
        all_pass = False
    
    print(f"{status} {repr(input_val):25} -> {repr(result):25} (Expected: {repr(expected)})")

print("\n" + "=" * 60)
if all_pass:
    print("SUCCESS! All tests pass with the refined fix.")
    print("\nThe fix handles whitespace correctly while preserving backwards compatibility.")
else:
    print("Some tests still fail. Further refinement needed.")