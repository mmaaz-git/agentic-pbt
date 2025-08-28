#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from pyatlan.model.utils import to_python_class_name

# Bug 1: Returns lowercase class name
result1 = to_python_class_name('0A')
print(f"Bug 1: to_python_class_name('0A') = '{result1}'")
print(f"  Starts with uppercase? {result1[0].isupper() if result1 else 'N/A'}")
print(f"  Is valid identifier? {result1.isidentifier() if result1 else 'N/A'}")

# Bug 2: Returns Python keyword
result2 = to_python_class_name('none')
print(f"\nBug 2: to_python_class_name('none') = '{result2}'")
try:
    exec(f"class {result2}: pass")
    print(f"  Can be used as class name: Yes")
except SyntaxError as e:
    print(f"  Can be used as class name: No - {e}")

# Let's check a few more edge cases
test_cases = ['0A', 'none', 'class', 'def', 'return', '123']
print("\nFull test results:")
for test in test_cases:
    result = to_python_class_name(test)
    print(f"  '{test}' -> '{result}'")
    if result:
        is_valid = result.isidentifier() and not __import__('keyword').iskeyword(result) and result[0].isupper()
        print(f"    Valid class name? {is_valid}")