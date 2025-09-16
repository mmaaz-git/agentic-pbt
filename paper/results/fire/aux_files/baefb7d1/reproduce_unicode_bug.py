#!/usr/bin/env python3
"""Minimal reproduction of the unicode character conversion bug."""

import fire.parser as parser

# Test the micro sign (µ) U+00B5
micro_sign = 'µ'  # U+00B5 MICRO SIGN
result = parser.DefaultParseValue(micro_sign)

print(f"Input: '{micro_sign}' (U+{ord(micro_sign):04X})")
print(f"Result: '{result}' (U+{ord(result):04X})")
print(f"Are they equal? {micro_sign == result}")

# Let's trace through what happens
import ast

# This is what happens inside _LiteralEval
root = ast.parse(micro_sign, mode='eval')
print(f"\nAST body type: {type(root.body)}")

if isinstance(root.body, ast.Name):
    print(f"AST Name.id: '{root.body.id}' (U+{ord(root.body.id):04X})")
    # The issue happens during ast.parse!
    
# Let's confirm this is an AST normalization issue  
print(f"\nDirect ast.parse comparison:")
print(f"ast.parse('µ').body.id == 'µ': {ast.parse('µ', mode='eval').body.id == 'µ'}")
print(f"ast.parse('µ').body.id == 'μ': {ast.parse('µ', mode='eval').body.id == 'μ'}")

# Test with other potentially problematic Unicode characters
test_chars = [
    ('µ', 'U+00B5', 'MICRO SIGN'),
    ('Å', 'U+00C5', 'LATIN CAPITAL LETTER A WITH RING ABOVE'),
    ('É', 'U+00C9', 'LATIN CAPITAL LETTER E WITH ACUTE'),
]

print("\n\nTesting other Unicode characters:")
for char, code, name in test_chars:
    result = parser.DefaultParseValue(char)
    print(f"{char} ({code} {name}) -> {result} (U+{ord(result):04X}) | Equal: {char == result}")