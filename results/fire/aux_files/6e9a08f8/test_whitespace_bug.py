#!/usr/bin/env python3
"""Investigate whitespace handling bug in fire.parser."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import parser

# Test whitespace handling
test_cases = [
    ('42', 42),
    (' 42', '???'),  # What does this return?
    ('42 ', '???'),  # What does this return?
    (' 42 ', '???'),  # What does this return?
    ('  42  ', '???'),  # What does this return?
    ('\t42\t', '???'),  # Tabs?
    (' True ', '???'),  # Boolean with spaces
    (' None ', '???'),  # None with spaces
    (' "hello" ', '???'),  # Quoted string with spaces
    (' [1, 2] ', '???'),  # List with spaces
]

print("Testing whitespace handling in DefaultParseValue:")
print("-" * 60)

for input_str, expected in test_cases:
    result = parser.DefaultParseValue(input_str)
    result_type = type(result).__name__
    print(f"Input: {repr(input_str):15} -> Result: {repr(result):15} (type: {result_type})")

print("\n" + "=" * 60)
print("Testing if leading/trailing whitespace affects parsing:")
print("-" * 60)

# More systematic test
values_to_test = ['42', 'True', 'False', 'None', '"hello"', '[1, 2]', '{"a": 1}']

for value in values_to_test:
    no_space = parser.DefaultParseValue(value)
    with_space = parser.DefaultParseValue(f'  {value}  ')
    
    if no_space == with_space:
        print(f"✓ '{value}' - Consistent (both parse to {repr(no_space)})")
    else:
        print(f"✗ '{value}' - INCONSISTENT!")
        print(f"  Without spaces: {repr(no_space)} (type: {type(no_space).__name__})")
        print(f"  With spaces:    {repr(with_space)} (type: {type(with_space).__name__})")