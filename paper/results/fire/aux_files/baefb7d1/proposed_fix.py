#!/usr/bin/env python3
"""Proposed fix for the Unicode normalization bug in fire.parser."""

import ast
import sys
import unicodedata

if sys.version_info[0:2] < (3, 8):
    _StrNode = ast.Str
else:
    _StrNode = ast.Constant


def _Replacement_fixed(node, original_source=None):
    """Fixed version of _Replacement that preserves Unicode characters.
    
    Args:
        node: A node of type Name. Could be a variable, or builtin constant.
        original_source: The original source string being parsed (optional).
    Returns:
        A node to use in place of the supplied Node. Either the same node, or a
        String node whose value matches the Name node's id.
    """
    value = node.id
    # These are the only builtin constants supported by literal_eval.
    if value in ('True', 'False', 'None'):
        return node
    
    # Check if Unicode normalization changed the identifier
    if original_source is not None:
        # Extract the substring from original source that corresponds to this node
        if hasattr(node, 'col_offset') and hasattr(node, 'end_col_offset'):
            original_text = original_source[node.col_offset:node.end_col_offset]
            # If the normalized identifier differs from original, preserve original
            if original_text != value:
                return _StrNode(original_text)
    
    return _StrNode(value)


def _LiteralEval_fixed(value):
    """Fixed version of _LiteralEval that preserves Unicode characters."""
    root = ast.parse(value, mode='eval')
    if isinstance(root.body, ast.BinOp):
        raise ValueError(value)

    for node in ast.walk(root):
        for field, child in ast.iter_fields(node):
            if isinstance(child, list):
                for index, subchild in enumerate(child):
                    if isinstance(subchild, ast.Name):
                        child[index] = _Replacement_fixed(subchild, value)

            elif isinstance(child, ast.Name):
                replacement = _Replacement_fixed(child, value)
                setattr(node, field, replacement)

    return ast.literal_eval(root)


def DefaultParseValue_fixed(value):
    """Fixed version of DefaultParseValue that preserves Unicode characters."""
    # Note: _LiteralEval will treat '#' as the start of a comment.
    try:
        return _LiteralEval_fixed(value)
    except (SyntaxError, ValueError):
        # If _LiteralEval can't parse the value, treat it as a string.
        return value


# Test the fix
if __name__ == "__main__":
    test_cases = [
        'µ',  # The problematic micro sign
        'hello',  # Normal string
        '123',  # Number
        '[1, 2, 3]',  # List
        'True',  # Boolean
        '{a: 1, b: 2}',  # Dict with barewords
    ]
    
    from fire.parser import DefaultParseValue
    
    print("Testing the fix:\n")
    print("=" * 70)
    for test in test_cases:
        original = DefaultParseValue(test)
        fixed = DefaultParseValue_fixed(test)
        
        print(f"Input: '{test}'")
        print(f"  Original: {repr(original)}")
        print(f"  Fixed:    {repr(fixed)}")
        
        if test == 'µ':
            if original != test and fixed == test:
                print(f"  ✅ Fix successful! Preserves Unicode character")
            else:
                print(f"  ❌ Fix didn't work as expected")
        elif original != fixed:
            print(f"  ⚠️  Fix changed behavior for this case")
        else:
            print(f"  ✓ Behavior unchanged")
        print("-" * 70)