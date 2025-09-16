#!/usr/bin/env python3
import sys
import ast
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import parser

# Let's trace what happens when we parse '{as: 0}'
input_str = '{as: 0}'

# Step 1: First, DefaultParseValue tries _LiteralEval
print("Testing what happens with '{as: 0}':")
print("-" * 40)

try:
    # This is what DefaultParseValue does internally
    result = parser._LiteralEval(input_str)
    print(f"_LiteralEval succeeded: {result}")
except (SyntaxError, ValueError) as e:
    print(f"_LiteralEval failed: {e}")
    print(f"Error type: {type(e).__name__}")
    
# Let's manually trace what _LiteralEval does
print("\nManual trace of _LiteralEval:")
print("-" * 40)

try:
    # Parse as AST
    root = ast.parse(input_str, mode='eval')
    print(f"AST parse succeeded: {ast.dump(root)}")
    
    # The function walks the AST and replaces Names with Strings
    # But 'as' is a keyword, so it can't be a Name
except SyntaxError as e:
    print(f"AST parse failed: {e}")

# Let's test with valid syntax
print("\nTesting with quotes around 'as':")
print("-" * 40)
input_str2 = '{"as": 0}'
result2 = parser.DefaultParseValue(input_str2)
print(f"Input: {input_str2}")
print(f"Result: {result2}")
print(f"Type: {type(result2)}")

# Testing Python keywords
import keyword
print("\nPython keywords that fail:")
print("-" * 40)
keywords_to_test = ['as', 'if', 'for', 'def', 'class', 'with', 'while', 'return', 'import']
for kw in keywords_to_test:
    if keyword.iskeyword(kw):
        test_str = f'{{{kw}: 0}}'
        result = parser.DefaultParseValue(test_str)
        is_dict = isinstance(result, dict)
        print(f"  {kw:10} -> {'dict' if is_dict else 'str '}")
        
print("\nThis is a BUG! Fire claims to support YAML-like syntax {a: b},")
print("but it fails when 'a' is a Python keyword.")
print("The documentation suggests it should work for any bareword key.")