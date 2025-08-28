#!/usr/bin/env python3
"""Simple test runner for codeconnections tests"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import required modules
from hypothesis import given, strategies as st, settings, example
import re
from troposphere import Tags
from troposphere.codeconnections import Connection

# Test 1: Round-trip property
print("Test 1: Round-trip property...")
try:
    conn = Connection("TestConn", ConnectionName="test-connection")
    d = conn.to_dict()
    props = d.get('Properties', {})
    conn2 = Connection.from_dict("TestConn", props)
    assert conn == conn2
    print("  Basic round-trip: PASSED")
except Exception as e:
    print(f"  Basic round-trip: FAILED - {e}")

# Test 2: Required property validation
print("\nTest 2: Required property validation...")
try:
    conn = Connection("TestConn")  # Missing required ConnectionName
    try:
        conn.to_dict()
        print("  FAILED - No error raised for missing ConnectionName")
    except ValueError as e:
        if "ConnectionName" in str(e) and "required" in str(e):
            print("  PASSED - Correctly raised error for missing ConnectionName")
        else:
            print(f"  FAILED - Wrong error: {e}")
except Exception as e:
    print(f"  FAILED - Unexpected error: {e}")

# Test 3: Title validation
print("\nTest 3: Title validation...")
try:
    # Valid title
    conn = Connection("ValidTitle123", ConnectionName="test")
    conn.validate_title()
    print("  Valid title: PASSED")
    
    # Invalid title with special characters
    conn = Connection("Invalid-Title!", ConnectionName="test")
    try:
        conn.validate_title()
        print("  FAILED - No error for invalid title")
    except ValueError as e:
        if "not alphanumeric" in str(e):
            print("  Invalid title rejection: PASSED")
        else:
            print(f"  FAILED - Wrong error: {e}")
except Exception as e:
    print(f"  FAILED - Unexpected error: {e}")

# Test 4: Tags concatenation
print("\nTest 4: Tags concatenation...")
try:
    t1 = Tags(Key1="Value1", Key2="Value2")
    t2 = Tags(Key3="Value3", Key4="Value4")
    combined = t1 + t2
    combined_dict = combined.to_dict()
    
    if len(combined_dict) == 4:
        print("  Tags concatenation count: PASSED")
    else:
        print(f"  FAILED - Expected 4 tags, got {len(combined_dict)}")
        
    # Check order preservation
    if combined_dict[0]['Key'] == 'Key1' and combined_dict[-1]['Key'] == 'Key4':
        print("  Tags order preservation: PASSED")
    else:
        print("  FAILED - Tags order not preserved")
except Exception as e:
    print(f"  FAILED - Unexpected error: {e}")

# Test 5: Type validation
print("\nTest 5: Type validation...")
try:
    conn = Connection("TestConn")
    try:
        conn.ConnectionName = 123  # Should be string
        print("  FAILED - No error for integer ConnectionName")
    except TypeError as e:
        if "ConnectionName" in str(e) and "str" in str(e):
            print("  Type validation: PASSED")
        else:
            print(f"  FAILED - Wrong error: {e}")
except Exception as e:
    print(f"  FAILED - Unexpected error: {e}")

# Test 6: Empty title handling
print("\nTest 6: Empty title handling...")
try:
    conn = Connection("", ConnectionName="test")
    try:
        conn.validate_title()
        print("  FAILED - No error for empty title")
    except ValueError as e:
        if "not alphanumeric" in str(e):
            print("  Empty title rejection: PASSED")
        else:
            print(f"  FAILED - Wrong error: {e}")
except Exception as e:
    print(f"  FAILED - Unexpected error: {e}")

# Test 7: Tags with non-string keys
print("\nTest 7: Tags with non-string keys...")
try:
    # This tests the handling of non-sortable keys
    tags = Tags(**{1: "Value1", 2: "Value2"})
    tags_dict = tags.to_dict()
    if len(tags_dict) == 2:
        print("  Non-string keys handling: PASSED")
    else:
        print(f"  FAILED - Expected 2 tags, got {len(tags_dict)}")
except Exception as e:
    print(f"  FAILED - Unexpected error: {e}")

print("\n" + "="*50)
print("Basic tests completed!")