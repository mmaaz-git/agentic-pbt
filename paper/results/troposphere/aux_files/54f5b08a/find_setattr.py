#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Read the source file and find __setattr__
with open('/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages/troposphere/__init__.py', 'r') as f:
    lines = f.readlines()

# Find the __setattr__ method
for i, line in enumerate(lines):
    if "def __setattr__" in line:
        print(f"Found __setattr__ at line {i+1}:")
        print("Method implementation:")
        # Print the method
        indent = len(line) - len(line.lstrip())
        for j in range(i, min(len(lines), i+50)):
            current_line = lines[j]
            # Stop if we hit another method at the same indentation level
            if j > i and current_line.strip() and not current_line.startswith(' ' * (indent + 1)):
                if not current_line.startswith(' ' * indent) or current_line.strip().startswith('def '):
                    break
            print(f"{j+1}: {lines[j].rstrip()}")
        break