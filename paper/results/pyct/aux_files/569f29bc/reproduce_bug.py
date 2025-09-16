#!/usr/bin/env python3
"""Minimal reproduction of the bug in pyct.report"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

import io
from pyct.report import report

print("Bug Reproduction: Package name containing ' # ' breaks output format")
print("=" * 70)

# The bug: when package name contains ' # ', the output format breaks
test_package = "package # comment"

print(f"Testing with package name: '{test_package}'")
print()

captured_output = io.StringIO()
sys.stdout = captured_output
try:
    report(test_package)
finally:
    sys.stdout = sys.__stdout__

output = captured_output.getvalue().strip()

print(f"Output: {output}")
print()

# Try to parse the output as intended
print("Attempting to parse output with ' # ' as separator:")
parts = output.split(' # ')
print(f"Number of parts: {len(parts)}")
for i, part in enumerate(parts):
    print(f"  Part {i}: '{part}'")

print()
print("Analysis:")
print("  The format string used is: \"{0:30} # {1}\"")
print("  Where {0} is 'package=version' and {1} is 'location'")
print()
print("  When package name is 'package # comment':")
print("    {0} becomes 'package # comment=unknown'")
print("    After formatting: 'package # comment=unknown      # not installed in this environment'")
print()
print("  This creates ambiguity when parsing with ' # ' as separator!")
print("  We get 3 parts instead of expected 2:")
print("    1. 'package'")
print("    2. 'comment=unknown     '")  
print("    3. 'not installed in this environment'")
print()
print("This is a BUG: The output format is ambiguous when package names contain ' # '")