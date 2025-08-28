#!/usr/bin/env python3
"""Minimal reproduction of the title validation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.nimblestudio as nimblestudio

# The character '¹' (superscript 1) is considered alphanumeric by Python
test_char = '¹'
print(f"Python's isalnum() says '{test_char}' is alphanumeric: {test_char.isalnum()}")

# But troposphere rejects it
try:
    component = nimblestudio.StudioComponent(
        title=test_char,
        Name="TestName",
        StudioId="TestStudio",
        Type="SHARED_FILE_SYSTEM"
    )
    print("Component created successfully")
except ValueError as e:
    print(f"ValueError raised: {e}")

# Let's also check the regex directly
import re
valid_names = re.compile(r"^[a-zA-Z0-9]+$")
print(f"Troposphere regex matches '{test_char}': {bool(valid_names.match(test_char))}")

# This shows the inconsistency - Python's isalnum() and troposphere's regex disagree