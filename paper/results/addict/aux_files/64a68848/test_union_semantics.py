#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/addict_env/lib/python3.13/site-packages')

from addict import Dict

# Test: Dict union should match standard dict union semantics
print("Testing Dict union semantics vs standard dict union:\n")

test_cases = [
    ({0: {0: None}}, {0: {}}),
    ({'a': {'b': 1}}, {'a': {'c': 2}}),
    ({'x': {'y': 'old'}}, {'x': 'new'}),
    ({'data': {'nested': {'deep': 1}}}, {'data': {}}),
]

for data1, data2 in test_cases:
    # Standard dict behavior
    std_d1 = dict(data1)
    std_d2 = dict(data2)
    std_result = std_d1 | std_d2
    
    # Addict Dict behavior
    add_d1 = Dict(data1)
    add_d2 = Dict(data2)
    add_result = add_d1 | add_d2
    
    print(f"d1: {data1}")
    print(f"d2: {data2}")
    print(f"Standard dict union: {std_result}")
    print(f"Addict Dict union:   {dict(add_result)}")
    
    # Check if they match
    matches = dict(add_result) == std_result
    print(f"Match: {matches}")
    if not matches:
        print(">>> BUG: Dict union doesn't match standard dict semantics!")
    print("-" * 60)
    print()

print("\nConclusion:")
print("The Dict class's union operator (|) violates Python's standard dict union semantics.")
print("Standard dict union does simple replacement: d1 | d2 means d2's values override d1's.")
print("But Dict's union uses update(), which recursively merges nested dicts instead of replacing them.")
print("This is a contract violation - users expect | to behave like standard dict union.")