#!/usr/bin/env python3
"""Minimal reproduction of the title validation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.opensearchserverless as oss

# This character is considered alphanumeric by Python
title = "Collection¹"
print(f"Is '{title}' alphanumeric according to Python? {title.isalnum()}")

# But troposphere rejects it with a misleading error message
try:
    collection = oss.Collection(
        title=title,
        Name="test-collection"
    )
    print("Collection created successfully")
except ValueError as e:
    print(f"Error: {e}")
    print("\nThe error says 'not alphanumeric' but the string IS alphanumeric")
    print("according to Python's str.isalnum() method.")