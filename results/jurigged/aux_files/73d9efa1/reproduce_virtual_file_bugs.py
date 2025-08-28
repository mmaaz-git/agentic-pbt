#!/usr/bin/env python3
"""
Reproduction of bugs in jurigged.recode.virtual_file function.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.recode import virtual_file
import linecache

print("=== Bug 1: virtual_file doesn't handle angle brackets properly ===")
# When name contains '<' or '>', the filename format is broken

name = "<"
contents = "test"
filename = virtual_file(name, contents)
print(f"Input name: {repr(name)}")
print(f"Generated filename: {repr(filename)}")
print(f"Expected format: <name#number>")
print(f"Count of '<': {filename.count('<')} (expected: 1)")
print(f"Count of '>': {filename.count('>')} (expected: 1)")

print("\n=== Bug 2: virtual_file with '>' in name ===")
name = ">"
filename = virtual_file(name, contents)
print(f"Input name: {repr(name)}")
print(f"Generated filename: {repr(filename)}")
print(f"Count of '<': {filename.count('<')} (expected: 1)")
print(f"Count of '>': {filename.count('>')} (expected: 1)")

print("\n=== Bug 3: Combined angle brackets ===")
name = "<test>"
filename = virtual_file(name, contents)
print(f"Input name: {repr(name)}")
print(f"Generated filename: {repr(filename)}")
print(f"Count of '<': {filename.count('<')} (expected: 1)")
print(f"Count of '>': {filename.count('>')} (expected: 1)")

print("\n=== Bug 4: Newline in name breaks pattern ===")
name = "\n"
filename = virtual_file(name, contents)
print(f"Input name: {repr(name)}")
print(f"Generated filename: {repr(filename)}")

# Try to extract name back using regex
import re
match = re.match(r'^<(.*)#\d+>$', filename)
print(f"Regex match (without DOTALL): {match}")
match_dotall = re.match(r'^<(.*)#\d+>$', filename, re.DOTALL)
print(f"Regex match (with DOTALL): {match_dotall}")
if match_dotall:
    print(f"Extracted name: {repr(match_dotall.group(1))}")

print("\n=== Impact ===")
print("These bugs could cause issues when:")
print("1. The filename is parsed or displayed")
print("2. Multiple angle brackets could confuse parsing logic")
print("3. Newlines in filenames could break line-based tools")
print("4. The format inconsistency could break assumptions in other code")