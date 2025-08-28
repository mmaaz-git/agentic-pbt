#!/usr/bin/env python3
"""Minimal reproduction of the comma bug in fire.interact._AvailableString"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
from fire import interact

# Create variables with comma in the name (valid Python)
variables = {
    'var_a': 1,
    'var,b': 2,  # This variable name contains a comma
    'var_c': 3
}

# Get the formatted output
output = interact._AvailableString(variables, verbose=False)
print("Output from _AvailableString:")
print(output)

# Try to parse the output to recover variable names
lines = output.split('\n')
for line in lines:
    if 'Objects:' in line:
        items_str = line.split(':', 1)[1].strip()
        parsed_vars = [item.strip() for item in items_str.split(',')]
        
        print("\nOriginal variables:", set(variables.keys()))
        print("Parsed variables:", set(parsed_vars))
        print("\nProblem: The variable 'var,b' gets split into 'var' and 'b'!")
        print("This creates ambiguous output that cannot be reliably parsed.")