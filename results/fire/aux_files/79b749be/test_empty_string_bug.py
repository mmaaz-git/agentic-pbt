#!/usr/bin/env python3
"""Comprehensive test demonstrating the empty string key bug in fire.interact."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

import fire.interact as interact

# Multiple test cases showing the bug
test_cases = [
    {'': 'value1'},
    {'': 'value1', 'a': 'value2'},
    {'a': 'value1', '': 'value2', 'b': 'value3'},
    {'': None, 'x': 1, 'y': 2},
]

for i, variables in enumerate(test_cases, 1):
    print(f"Test case {i}: {variables}")
    result = interact._AvailableString(variables, verbose=False)
    print(result)
    print("-" * 40)
    
    # Check if empty string appears in the output
    if variables:
        if any(k for k in variables if k and not k.startswith('_')):
            # If there are other visible keys
            if 'Objects:' in result:
                objects_line = [line for line in result.split('\n') if line.startswith('Objects:')][0]
                items_part = objects_line.split(': ', 1)[1]
                # This will show the malformed output with extra comma/space
                print(f"Items part: '{items_part}'")
                if items_part.startswith(', '):
                    print("BUG: Extra comma at start!")
                if ', ,' in items_part:
                    print("BUG: Double comma in middle!")
                if items_part.endswith(', '):
                    print("BUG: Extra comma at end!")
    print("=" * 40 + "\n")