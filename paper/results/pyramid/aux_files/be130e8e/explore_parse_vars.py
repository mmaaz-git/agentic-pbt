#!/usr/bin/env python3
"""Explore potential bugs in parse_vars."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.scripts.common import parse_vars

# Test various edge cases
test_cases = [
    # Basic cases
    (['a=b'], {'a': 'b'}),
    (['a=b', 'c=d'], {'a': 'b', 'c': 'd'}),
    
    # Empty values and keys
    (['=value'], {'': 'value'}),
    (['key='], {'key': ''}),
    (['='], {'': ''}),
    
    # Multiple equals
    (['key=val=ue'], {'key': 'val=ue'}),
    (['key=a=b=c=d'], {'key': 'a=b=c=d'}),
    
    # Special characters
    (['key with spaces=value with spaces'], {'key with spaces': 'value with spaces'}),
    (['key\t=\tvalue'], {'key\t': '\tvalue'}),
    (['key\n=\nvalue'], {'key\n': '\nvalue'}),
    
    # Unicode
    (['🦄=🎉'], {'🦄': '🎉'}),
    (['key=值'], {'key': '值'}),
    
    # Duplicates
    (['key=first', 'key=second'], {'key': 'second'}),
    (['a=1', 'b=2', 'a=3'], {'a': '3', 'b': '2'}),
]

print("Testing parse_vars edge cases...")
print("=" * 50)

for i, (input_list, expected) in enumerate(test_cases, 1):
    try:
        result = parse_vars(input_list)
        if result == expected:
            print(f"Test {i}: ✓ PASS")
            print(f"  Input: {input_list}")
            print(f"  Result: {result}")
        else:
            print(f"Test {i}: ✗ FAIL")
            print(f"  Input: {input_list}")
            print(f"  Expected: {expected}")
            print(f"  Got: {result}")
    except Exception as e:
        print(f"Test {i}: ✗ ERROR")
        print(f"  Input: {input_list}")
        print(f"  Error: {e}")
    print()

# Test error cases
print("\nTesting error cases...")
print("=" * 50)

error_cases = [
    ['no_equals'],
    [''],
    ['multiple', 'no_equals'],
]

for i, input_list in enumerate(error_cases, 1):
    try:
        result = parse_vars(input_list)
        print(f"Error test {i}: ✗ Should have raised ValueError")
        print(f"  Input: {input_list}")
        print(f"  Got: {result}")
    except ValueError as e:
        print(f"Error test {i}: ✓ Correctly raised ValueError")
        print(f"  Input: {input_list}")
        print(f"  Error: {e}")
    except Exception as e:
        print(f"Error test {i}: ✗ Unexpected error")
        print(f"  Input: {input_list}")
        print(f"  Error: {e}")
    print()