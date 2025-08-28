#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/addict_env/lib/python3.13/site-packages')

from addict import Dict
import copy

print("Testing |= operator (in-place union):\n")

# Test case where bug occurs
data1 = {'a': {'b': 1, 'c': 2}}
data2 = {'a': {'d': 3}}

# Standard dict behavior
std_d1 = dict(data1)
std_d1_copy = copy.deepcopy(std_d1)
std_d2 = dict(data2)
std_d1 |= std_d2

# Addict Dict behavior  
add_d1 = Dict(data1)
add_d1_copy = Dict(copy.deepcopy(data1))
add_d2 = Dict(data2)
add_d1 |= add_d2

print(f"Original d1: {data1}")
print(f"d2: {data2}")
print()
print(f"Standard dict after d1 |= d2: {std_d1}")
print(f"Addict Dict after d1 |= d2:   {dict(add_d1)}")
print()
print(f"Match: {dict(add_d1) == std_d1}")

if dict(add_d1) != std_d1:
    print(">>> BUG: Dict |= operator also doesn't match standard dict semantics!")