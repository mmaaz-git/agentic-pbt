import os
import re

# Find actual usage of dispatch_hook in sessions.py
sessions_file = "/home/linuxbrew/.linuxbrew/lib/python3.13/site-packages/requests/sessions.py"

with open(sessions_file, 'r') as f:
    lines = f.readlines()
    
# Find the line with dispatch_hook
for i, line in enumerate(lines, 1):
    if 'dispatch_hook' in line and not line.strip().startswith('#'):
        # Print context
        start = max(0, i-6)
        end = min(len(lines), i+5)
        print(f"Found dispatch_hook usage at line {i}:")
        print("="*50)
        for j in range(start, end):
            prefix = ">>> " if j == i-1 else "    "
            print(f"{prefix}{j+1}: {lines[j]}", end="")
        print("="*50)
        print()

# Also check how hooks are initialized and passed
print("\nLooking for how hooks are passed to dispatch_hook...")
for i, line in enumerate(lines, 1):
    if 'hooks' in line and ('self.hooks' in line or 'hooks=' in line):
        if i > 700 and i < 715:  # Around the dispatch_hook call
            print(f"Line {i}: {line.strip()}")