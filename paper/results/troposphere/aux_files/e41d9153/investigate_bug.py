#!/usr/bin/env python3
"""Investigate why the empty title bug occurs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere
from troposphere import Parameter

print("Investigating the empty title bug...")
print("-" * 40)

# Create parameter with empty title
param = Parameter("", Type="String")

# Check if validate_title is being called
print(f"Parameter title: '{param.title}'")
print(f"Does parameter have validate_title method? {hasattr(param, 'validate_title')}")

# Try calling validate_title directly
print("\nCalling validate_title() directly...")
try:
    param.validate_title()
    print("  validate_title() did not raise an error!")
except ValueError as e:
    print(f"  validate_title() raised: {e}")

# Check the validation condition
print("\nChecking the validation condition:")
print(f"  bool(not param.title) = {bool(not param.title)}")
print(f"  bool('') = {bool('')}")  # Empty string is falsy
print(f"  not '' = {not ''}")  # This should be True

# The issue seems to be that validate_title() is called but doesn't raise
# Let's check the actual condition in the code
import re
valid_names = re.compile(r"^[a-zA-Z0-9]+$")
title = ""

print(f"\nActual validation check:")
print(f"  title = '{title}'")
print(f"  not title = {not title}")
print(f"  valid_names.match(title) = {valid_names.match(title)}")
print(f"  not valid_names.match(title) = {not valid_names.match(title)}")

# The condition is: if not self.title or not valid_names.match(self.title)
should_fail = not title or not valid_names.match(title)
print(f"  Condition (not title or not valid_names.match(title)) = {should_fail}")

if should_fail:
    print("\nThe condition evaluates to True, so it SHOULD raise ValueError")
    print("But it doesn't! This confirms the bug.")

# Let's check when validate_title is called
print("\nChecking when validate_title is called in __init__...")
print("Looking at the BaseAWSObject.__init__ method (line 183-184):")
print("  # try to validate the title if its there")
print("  if self.title:")
print("      self.validate_title()")
print("\nAH! There's the bug!")
print("The code checks 'if self.title:' before calling validate_title()")
print("An empty string is falsy, so validate_title() is never called!")
print("\nThis is a logic bug in the initialization code.")