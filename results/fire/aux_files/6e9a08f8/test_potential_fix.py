#!/usr/bin/env python3
"""Test a potential fix for the whitespace bug."""

import sys
import ast
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

def DefaultParseValue_Fixed(value):
    """Fixed version that strips leading/trailing whitespace before parsing."""
    # Strip whitespace before attempting to parse
    stripped_value = value.strip()
    
    try:
        return _LiteralEval(stripped_value)
    except (SyntaxError, ValueError):
        # If parsing fails, return the original value (not stripped)
        # to maintain backwards compatibility for actual string inputs
        return value

def _LiteralEval(value):
    """Copy of the original _LiteralEval for testing."""
    root = ast.parse(value, mode='eval')
    if isinstance(root.body, ast.BinOp):
        raise ValueError(value)
    
    for node in ast.walk(root):
        for field, child in ast.iter_fields(node):
            if isinstance(child, list):
                for index, subchild in enumerate(child):
                    if isinstance(subchild, ast.Name):
                        child[index] = _Replacement(subchild)
            elif isinstance(child, ast.Name):
                replacement = _Replacement(child)
                setattr(node, field, replacement)
    
    return ast.literal_eval(root)

def _Replacement(node):
    """Copy of the original _Replacement."""
    value = node.id
    if value in ('True', 'False', 'None'):
        return node
    # Simplified replacement for testing
    if sys.version_info[0:2] < (3, 8):
        return ast.Str(value)
    else:
        return ast.Constant(value)

# Test the fix
print("Testing the fixed version:")
print("-" * 60)

test_cases = [
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
    # Edge case: actual strings with spaces should be preserved
    ('  not_a_literal  ', '  not_a_literal  '),  # Can't be parsed, so returned as-is
]

all_pass = True
for input_val, expected in test_cases:
    result = DefaultParseValue_Fixed(input_val)
    
    if result == expected:
        print(f"✓ {repr(input_val):20} -> {repr(result):20} (Expected: {repr(expected)})")
    else:
        print(f"✗ {repr(input_val):20} -> {repr(result):20} (Expected: {repr(expected)})")
        all_pass = False

print("\n" + "=" * 60)
if all_pass:
    print("All tests pass! The fix works correctly.")
    print("\nSuggested fix: Add value.strip() before parsing in _LiteralEval or DefaultParseValue")
else:
    print("Some tests failed. The fix needs adjustment.")