#!/usr/bin/env python3
"""Investigate the title validation bug in troposphere."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import re
import troposphere.applicationinsights as appinsights

# The problematic character
title = '¹'

print(f"Testing title: {title!r}")
print(f"  title.isalnum() = {title.isalnum()}")
print(f"  title.isalpha() = {title.isalpha()}")
print(f"  title.isdigit() = {title.isdigit()}")
print(f"  title.isnumeric() = {title.isnumeric()}")
print()

# Check the regex pattern used in troposphere
valid_names = re.compile(r"^[a-zA-Z0-9]+$")
print(f"Regex pattern: r'^[a-zA-Z0-9]+$'")
print(f"  Regex matches: {bool(valid_names.match(title))}")
print()

# Try creating an Application with this title
print("Attempting to create Application with title '¹'...")
try:
    app = appinsights.Application(
        title,
        ResourceGroupName="TestGroup"
    )
    print("✅ Application created successfully")
except ValueError as e:
    print(f"❌ Failed with error: {e}")
print()

# Test more Unicode alphanumeric characters
test_chars = ['¹', '²', '³', 'ᴬ', 'ᵇ', 'α', 'β', '一', '二', 'Ⅰ', 'Ⅱ']
print("Testing various Unicode alphanumeric characters:")
print("-" * 50)

for char in test_chars:
    is_alnum = char.isalnum()
    regex_match = bool(valid_names.match(char))
    
    print(f"Character: {char!r}")
    print(f"  .isalnum() = {is_alnum}")
    print(f"  Regex match = {regex_match}")
    
    if is_alnum != regex_match:
        print(f"  ⚠️  MISMATCH: Python says alphanumeric={is_alnum}, regex says={regex_match}")
    
    try:
        app = appinsights.Application(char, ResourceGroupName="Test")
        status = "✅ Accepted"
    except ValueError:
        status = "❌ Rejected"
    print(f"  Status: {status}")
    print()

print("\nCONCLUSION:")
print("-" * 50)
print("There is a discrepancy between Python's isalnum() method and the")
print("regex pattern ^[a-zA-Z0-9]+$ used in troposphere's validate_title().")
print()
print("Python's isalnum() returns True for Unicode alphanumeric characters")
print("(including superscripts, subscripts, and non-ASCII letters/digits),")
print("while the regex only matches ASCII alphanumeric characters [a-zA-Z0-9].")