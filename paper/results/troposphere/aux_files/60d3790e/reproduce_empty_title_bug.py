#!/usr/bin/env python3
"""
Test empty title handling in troposphere
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.codeconnections import Connection

# Test with completely empty title
print("Test 1: Empty string title")
try:
    conn = Connection("", ConnectionName="ValidConnectionName")
    result = conn.to_dict(validation=True)
    print(f"BUG: Empty title accepted, result: {result}")
    
    try:
        conn.validate_title()
    except ValueError as e:
        print(f"validate_title() rejects it: {e}")
except Exception as e:
    print(f"Error: {e}")

# Test with None title
print("\nTest 2: None as title")
try:
    conn = Connection(None, ConnectionName="ValidConnectionName")
    result = conn.to_dict(validation=True)
    print(f"None title result: {result}")
except Exception as e:
    print(f"Error with None title: {e}")

# Test whitespace-only title
print("\nTest 3: Whitespace-only title")
try:
    conn = Connection("   ", ConnectionName="ValidConnectionName")
    result = conn.to_dict(validation=True)
    print(f"BUG: Whitespace title accepted")
    
    try:
        conn.validate_title()
    except ValueError as e:
        print(f"validate_title() rejects it: {e}")
except Exception as e:
    print(f"Error: {e}")