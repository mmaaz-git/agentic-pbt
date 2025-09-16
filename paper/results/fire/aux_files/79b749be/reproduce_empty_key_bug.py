#!/usr/bin/env python3
"""Minimal reproduction of the empty string key bug in fire.interact."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

import fire.interact as interact

# Test with empty string key
variables = {'': 'empty_key_value', 'normal_key': 'normal_value'}

print("Testing with variables:", variables)
print("\n" + "="*50 + "\n")

result = interact._AvailableString(variables, verbose=False)
print(result)

print("="*50 + "\n")

# Notice how the empty string appears between "Objects:" and "normal_key"
# This makes it look like "Objects: , normal_key" with an extra comma
assert '' not in result.split('Objects: ')[1], "Empty string key should not appear in output"