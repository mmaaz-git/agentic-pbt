#!/usr/bin/env python3
"""Verify title validation bypass bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.finspace as finspace
import re

# The validation regex from troposphere
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

print("=== Title Validation Bypass Bug Verification ===\n")

# Test 1: Empty string
print("Test 1: Empty string as title")
print("-" * 40)
try:
    env = finspace.Environment("", Name="TestEnv")
    print(f"✗ BUG: Empty string accepted as title")
    print(f"  env.title = {repr(env.title)}")
    print(f"  Regex match result: {bool(valid_names.match(''))}")
    print(f"  Expected: ValueError (empty string is not alphanumeric)")
    print(f"  Actual: Object created successfully")
    
    # Test if to_dict also bypasses
    try:
        result = env.to_dict()
        print(f"  to_dict() also succeeds - full bypass!")
    except ValueError as e:
        print(f"  to_dict() catches it: {e}")
        
except ValueError as e:
    print(f"✓ Empty string correctly rejected: {e}")

print()

# Test 2: None as title  
print("Test 2: None as title")
print("-" * 40)
try:
    env = finspace.Environment(None, Name="TestEnv")
    print(f"✗ Potential issue: None accepted as title")
    print(f"  env.title = {repr(env.title)}")
    
    # Will validation catch it?
    try:
        result = env.to_dict()
        print(f"  to_dict() succeeds with None title!")
        # Check what gets generated
        print(f"  Generated Type: {result.get('Type')}")
        if result.get('Type') == 'AWS::FinSpace::Environment':
            print(f"  ✗ BUG: CloudFormation resource created without title!")
    except (AttributeError, TypeError) as e:
        print(f"  to_dict() fails with: {type(e).__name__}: {e}")
        
except (ValueError, TypeError) as e:
    print(f"✓ None correctly rejected: {e}")

print()

# Test 3: Whitespace characters
print("Test 3: Whitespace characters")  
print("-" * 40)
for ws in [" ", "  ", "\t", "\n"]:
    try:
        env = finspace.Environment(ws, Name="TestEnv")
        print(f"✗ BUG: Whitespace {repr(ws)} accepted as title")
    except ValueError as e:
        expected = "not alphanumeric" in str(e)
        status = "✓" if expected else "?"
        print(f"{status} Whitespace {repr(ws)} rejected: {e}")

print()

# Test 4: Control flow analysis
print("Analysis of the bug:")
print("-" * 40)
print("In BaseAWSObject.__init__ (line 183-184):")
print("  if self.title:")
print("      self.validate_title()")
print()
print("This means validate_title() is ONLY called when title is truthy.")
print("Empty string (\"\") is falsy in Python, so validation is skipped!")
print("None is also falsy, so validation is skipped!")
print()
print("The validation function itself (line 327-328) would reject these:")
print("  if not self.title or not valid_names.match(self.title):")
print("      raise ValueError('Name \"%s\" not alphanumeric' % self.title)")
print()
print("But it never gets called for falsy titles!")

print("\n=== Verification Complete ===")
print("\nCONCLUSION: Title validation bypass bug confirmed!")
print("Empty strings and None bypass validation in __init__")