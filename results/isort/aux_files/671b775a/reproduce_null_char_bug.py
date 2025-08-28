#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.io import File

# Minimal reproduction of null character in filename bug
filename_with_null = "test\x00.py"
content = "print('hello')"

try:
    file_obj = File.from_contents(content, filename_with_null)
    print(f"Created File object: {file_obj}")
except ValueError as e:
    print(f"Error: {e}")
    print("This is a bug - File.from_contents should handle or reject filenames with null characters gracefully")