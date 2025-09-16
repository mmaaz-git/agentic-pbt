#!/usr/bin/env python3
"""Minimal reproduction of title validation bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.ask as ask

# This character is alphanumeric according to Python's isalnum()
title = 'µ'
print(f"Is '{title}' alphanumeric according to Python? {title.isalnum()}")

# Try to create a Skill with this title
try:
    skill = ask.Skill(title)
    print(f"Successfully created skill with title: {title}")
except ValueError as e:
    print(f"Failed with error: {e}")
    print("\nBug: The error message says 'not alphanumeric' but the character IS alphanumeric according to Python's isalnum() method.")
    print("The actual validation uses ASCII-only regex, making the error message misleading.")