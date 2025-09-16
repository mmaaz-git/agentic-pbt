#!/usr/bin/env python3
"""Explore the sphinxcontrib.applehelp module to understand its structure and properties."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

import inspect
from sphinx.util.osutil import make_filename
from sphinxcontrib.applehelp import AppleHelpBuilder, setup

# Check make_filename function
print("=== make_filename ===")
print(f"Signature: {inspect.signature(make_filename)}")
print(f"Source:\n{inspect.getsource(make_filename)}")

print("\n=== AppleHelpBuilder Methods ===")
for name, method in inspect.getmembers(AppleHelpBuilder, predicate=inspect.isfunction):
    if not name.startswith('_'):
        print(f"{name}: {inspect.signature(method)}")

print("\n=== Setup function ===")
print(f"Signature: {inspect.signature(setup)}")

# Test imports and basic functionality
print("\n=== Testing imports ===")
import plistlib
print(f"plistlib available: {plistlib is not None}")

# Look for properties we can test
print("\n=== Looking for testable properties ===")
print("1. make_filename should create valid filenames from project names")
print("2. plistlib.dump/load round-trip for Info.plist")
print("3. shlex.quote should properly escape shell arguments")
print("4. Path manipulations should be consistent")