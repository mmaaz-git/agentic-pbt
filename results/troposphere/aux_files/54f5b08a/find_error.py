#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Read the source file and find the error
with open('/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages/troposphere/__init__.py', 'r') as f:
    lines = f.readlines()

# Find the line with the error message
for i, line in enumerate(lines):
    if "object does not support attribute" in line:
        print(f"Found at line {i+1}:")
        print("Context:")
        # Print surrounding lines for context
        start = max(0, i-10)
        end = min(len(lines), i+10)
        for j in range(start, end):
            marker = ">>> " if j == i else "    "
            print(f"{marker}{j+1}: {lines[j].rstrip()}")