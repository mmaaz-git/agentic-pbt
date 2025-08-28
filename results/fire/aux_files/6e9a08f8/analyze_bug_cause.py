#!/usr/bin/env python3
"""Analyze the cause of the whitespace bug."""

import sys
import ast
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import parser

# Let's trace what happens with leading whitespace
test_values = ['42', ' 42', '  42']

print("Tracing the parsing process:")
print("-" * 60)

for value in test_values:
    print(f"\nInput: {repr(value)}")
    
    # Try to parse with ast.parse directly
    try:
        root = ast.parse(value, mode='eval')
        print(f"  ast.parse succeeded - AST type: {type(root.body).__name__}")
        
        # Try literal_eval
        try:
            result = ast.literal_eval(value)
            print(f"  ast.literal_eval result: {repr(result)}")
        except:
            print(f"  ast.literal_eval failed")
            
        # Try the internal _LiteralEval
        try:
            result = parser._LiteralEval(value)
            print(f"  parser._LiteralEval result: {repr(result)}")
        except Exception as e:
            print(f"  parser._LiteralEval failed: {e}")
            
    except SyntaxError as e:
        print(f"  ast.parse failed with SyntaxError: {e}")
        print(f"  This causes DefaultParseValue to return the string as-is")
    
    # Show what DefaultParseValue returns
    final = parser.DefaultParseValue(value)
    print(f"  DefaultParseValue result: {repr(final)} (type: {type(final).__name__})")

print("\n" + "=" * 60)
print("Root cause analysis:")
print("-" * 60)
print("The issue is that ast.parse() fails on strings with leading whitespace")
print("when parsing in 'eval' mode. This causes a SyntaxError in _LiteralEval,") 
print("which DefaultParseValue catches and then returns the original string.")
print("\nThis is because in eval mode, Python expects a single expression,")
print("and leading whitespace is not allowed in that context.")