#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

# Check if there are any tests or examples that show expected behavior
import os
import glob

# Look for test files or example usage
test_patterns = [
    "/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages/**/test*.py",
    "/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages/**/example*.py",
]

for pattern in test_patterns:
    files = glob.glob(pattern, recursive=True)
    if files:
        print(f"Found files matching {pattern}:")
        for f in files[:5]:  # Limit to first 5
            print(f"  {f}")