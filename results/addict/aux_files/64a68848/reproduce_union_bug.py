#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/addict_env/lib/python3.13/site-packages')

from addict import Dict

# Minimal reproduction based on Hypothesis finding
data1 = {0: {0: None}}
data2 = {0: {}}

d1 = Dict(data1)
d2 = Dict(data2)

print("d1:", d1)
print("d2:", d2)
print()

# Test union operator
d3 = d1 | d2
print("d1 | d2:", d3)
print("d3[0]:", d3[0])
print("Type of d3[0]:", type(d3[0]))
print()

# Expected behavior: d2's value should override d1's value
print("Expected d3[0] to equal d2[0]:", d2[0])
print("Actual d3[0]:", d3[0])
print("Are they equal?", d3[0] == d2[0])
print()

# Let's compare with regular dict behavior
regular_d1 = dict(data1)
regular_d2 = dict(data2)
regular_d3 = regular_d1 | regular_d2
print("Regular dict union:")
print("regular_d1 | regular_d2:", regular_d3)
print("regular_d3[0]:", regular_d3[0])
print()

# Let's also test with update() method
d4 = Dict(data1)
d5 = Dict(data2)
d4.update(d5)
print("Using update() method:")
print("d4 after d4.update(d5):", d4)
print("d4[0]:", d4[0])
print()

# Check the __or__ implementation
print("Looking at __or__ implementation:")
print("Dict.__or__ method creates new Dict(self), then calls update(other)")
print("So the bug is likely in how update() handles nested empty dicts vs how union expects it to work")