#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import parser

# Bug: Fire's YAML-like dict parsing fails for Python keywords as keys

# Works for non-keywords
result1 = parser.DefaultParseValue('{foo: 1}')
assert isinstance(result1, dict) and result1 == {'foo': 1}
print("✓ {foo: 1} parsed correctly")

# Fails for Python keywords
result2 = parser.DefaultParseValue('{as: 2}')
assert isinstance(result2, str)  # Returns string instead of dict!
print("✗ {as: 2} NOT parsed as dict, returned as string:", result2)

# More keyword failures
keywords = ['if', 'for', 'def', 'class', 'with', 'while']
for kw in keywords:
    input_str = f'{{{kw}: 0}}'
    result = parser.DefaultParseValue(input_str)
    if not isinstance(result, dict):
        print(f"✗ {input_str} NOT parsed as dict")
    
print("\nExpected: All inputs should parse as dicts")
print("Actual: Python keywords cause parsing to fail")