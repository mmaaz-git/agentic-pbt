#!/usr/bin/env python3
import sys
import os

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/multi-key-dict_env/lib/python3.13/site-packages')

# Change to the working directory
os.chdir('/root/hypothesis-llm/worker_/1')

print("Executing bug finder tests...")
print("=" * 70)

# Read and execute the bug finder script
with open('hypothesis_bug_finder.py', 'r') as f:
    code = f.read()

# Execute the code
exec(code)

print("\nTests completed.")