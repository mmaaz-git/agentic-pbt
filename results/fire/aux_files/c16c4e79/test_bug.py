#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import parser

# Test the failing case
input_str = '{as: 0}'
result = parser.DefaultParseValue(input_str)

print(f"Input: {input_str}")
print(f"Result: {result}")
print(f"Type: {type(result)}")
print(f"Is dict: {isinstance(result, dict)}")

# Let's also test similar cases
test_cases = [
    '{a: 0}',
    '{as: 0}',
    '{ass: 0}',
    '{if: 0}',
    '{for: 0}',
    '{def: 0}',
    '{class: 0}',
]

print("\nTesting various cases:")
for test in test_cases:
    result = parser.DefaultParseValue(test)
    print(f"  {test:15} -> {type(result).__name__:6} {result}")