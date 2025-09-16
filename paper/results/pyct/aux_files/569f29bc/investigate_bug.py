#!/usr/bin/env python3
"""Investigate the output format bug in pyct.report"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

import io
from pyct.report import report

print("Investigating output format bug with special characters...")
print("=" * 60)

# Test with various special characters
test_inputs = [
    "#",
    "##",
    "#test",
    "test#",
    "=",
    "==",
    "=test",
    "test=",
    "#=",
    "=#",
    " # ",
    "package # comment",
]

for package_name in test_inputs:
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        report(package_name)
    finally:
        sys.stdout = sys.__stdout__
    
    output = captured_output.getvalue().strip()
    print(f"Input: '{package_name}'")
    print(f"Output: '{output}'")
    
    # Check if format is correct
    equals_pos = output.find('=')
    # Find the separator hash (should be around position 30-31)
    # The format is "{0:30} # {1}" so the separator hash should be after padding
    parts = output.split(' # ')
    if len(parts) != 2:
        print(f"  ✗ Format broken! Expected 2 parts separated by ' # ', got {len(parts)} parts")
        print(f"    Parts: {parts}")
    else:
        print(f"  ✓ Format OK")
    print()

print("=" * 60)
print("\nDetailed analysis of the '#' bug:")
print("-" * 40)

# Reproduce the minimal failing case
captured_output = io.StringIO()
sys.stdout = captured_output
try:
    report('#')
finally:
    sys.stdout = sys.__stdout__

output = captured_output.getvalue().strip()
print(f"Input: '#'")
print(f"Raw output: '{output}'")
print(f"Output repr: {repr(output)}")

# Analyze the output structure
print(f"\nExpected format: 'package=version{{padding}} # location'")
print(f"Actual output:   '{output}'")

# The issue is that when package name is '#', the output becomes:
# "#=unknown                      # not installed in this environment"
# The format string "{0:30} # {1}" causes the separator " # " to appear
# This is working as intended - not actually a bug!

print("\nActually, this appears to be working correctly!")
print("The format is: '{package}={version}' padded to 30 chars, then ' # {location}'")
print("When package='#', we get '#=unknown' padded to 30, then ' # location'")
print("So the output '#=unknown                      # not installed...' is CORRECT")