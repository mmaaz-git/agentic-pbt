#!/usr/bin/env python3
"""Minimal reproduction of the bug found in fire.decorators."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

import fire.decorators as decorators

# Create a simple test function
def test_func():
    return None

# Test with empty positional arguments
print("Testing SetParseFns with empty list...")
decorated = decorators.SetParseFns()(test_func)
parse_fns = decorators.GetParseFns(decorated)

print(f"Input positional_fns: []")
print(f"Result positional: {parse_fns['positional']}")
print(f"Type of result: {type(parse_fns['positional'])}")
print(f"Equal to []? {parse_fns['positional'] == []}")
print(f"Equal to ()? {parse_fns['positional'] == ()}")

print("\n" + "="*50 + "\n")

# Test with non-empty list
print("Testing SetParseFns with non-empty list...")
decorated2 = decorators.SetParseFns(str, int)(test_func)
parse_fns2 = decorators.GetParseFns(decorated2)

print(f"Input positional_fns: [str, int] (passed as *args)")
print(f"Result positional: {parse_fns2['positional']}")
print(f"Type of result: {type(parse_fns2['positional'])}")

print("\n" + "="*50 + "\n")

# Let's look at the source to understand the issue
print("Looking at SetParseFns implementation (line 68-73):")
print("""
def _Decorator(fn):
    parse_fns = GetParseFns(fn)
    parse_fns['positional'] = positional  # <-- Line 70
    parse_fns['named'].update(named)
    _SetMetadata(fn, FIRE_PARSE_FNS, parse_fns)
    return fn
""")

print("\nThe issue: 'positional' is the *args tuple from the decorator,")
print("so SetParseFns() creates positional=(), not positional=[]")
print("This is a type inconsistency!")