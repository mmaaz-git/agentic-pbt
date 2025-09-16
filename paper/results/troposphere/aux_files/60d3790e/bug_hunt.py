#!/usr/bin/env python3
"""Bug hunting in troposphere.codeconnections using property-based testing"""

import sys
import os
import traceback
from datetime import datetime
import random
import string

# Add the virtual env to path  
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, seed, Verbosity
from hypothesis.errors import InvalidArgument
import pytest

from troposphere import Tags
from troposphere.codeconnections import Connection

# Configure hypothesis
settings.register_profile("bug_hunt", max_examples=500, verbosity=Verbosity.verbose)
settings.load_profile("bug_hunt")

print("="*60)
print("Bug Hunting in troposphere.codeconnections")
print("="*60)

# Test 1: Edge case - empty title
print("\n[TEST 1] Testing empty title edge case...")
try:
    conn = Connection("", ConnectionName="test")
    try:
        conn.validate_title()
        print("  ✗ BUG FOUND: Empty title '' was accepted by validate_title()")
        print("    This violates the alphanumeric requirement")
        bug1_found = True
    except ValueError as e:
        print(f"  ✓ Empty title correctly rejected: {e}")
        bug1_found = False
except Exception as e:
    print(f"  ? Unexpected error: {e}")
    bug1_found = False

# Test 2: Whitespace-only titles
print("\n[TEST 2] Testing whitespace-only titles...")
whitespace_titles = ["   ", "\t", "\n", " \t\n "]
bugs_found = []
for title in whitespace_titles:
    try:
        conn = Connection(title, ConnectionName="test")
        result = conn.to_dict(validation=False)
        if 'Type' in result:
            print(f"  ✗ BUG: Whitespace title {repr(title)} was accepted")
            bugs_found.append(title)
    except Exception as e:
        pass

if bugs_found:
    print(f"  ✗ BUG FOUND: {len(bugs_found)} whitespace titles were accepted: {bugs_found}")
    bug2_found = True
else:
    print("  ✓ All whitespace titles correctly rejected")
    bug2_found = False

# Test 3: Title validation is not automatically called
print("\n[TEST 3] Testing if title validation is automatically enforced...")
try:
    # Create connection with invalid title containing special chars
    conn = Connection("test-conn-123", ConnectionName="myconn")
    # Try to convert to dict - does it validate the title?
    result = conn.to_dict(validation=True)
    print(f"  ✗ BUG FOUND: Invalid title 'test-conn-123' was not validated during to_dict()")
    print(f"    The title contains hyphens which violate alphanumeric requirement")
    print(f"    Result: {result}")
    bug3_found = True
except ValueError as e:
    if "not alphanumeric" in str(e):
        print("  ✓ Title validation correctly enforced")
        bug3_found = False
    else:
        print(f"  ? Different error: {e}")
        bug3_found = False

# Test 4: Round-trip with None values
print("\n[TEST 4] Testing round-trip with None values in optional fields...")
try:
    conn1 = Connection("Test", ConnectionName="test", HostArn=None)
    d = conn1.to_dict()
    props = d.get('Properties', {})
    conn2 = Connection.from_dict("Test", props)
    
    # Check if None is preserved or omitted
    if 'HostArn' in props and props['HostArn'] is None:
        print("  ! None value is included in dict")
    elif 'HostArn' not in props:
        print("  ! None value is omitted from dict")
    
    # Are they equal?
    if conn1 == conn2:
        print("  ✓ Round-trip with None successful")
        bug4_found = False
    else:
        print(f"  ✗ BUG: Round-trip with None failed")
        print(f"    Original: {conn1.to_json(validation=False)}")
        print(f"    After:    {conn2.to_json(validation=False)}")
        bug4_found = True
except Exception as e:
    print(f"  ? Error during round-trip: {e}")
    bug4_found = False

# Test 5: from_dict with extra fields
print("\n[TEST 5] Testing from_dict with unexpected fields...")
try:
    extra_props = {
        'ConnectionName': 'test',
        'ExtraField': 'should-not-exist',
        'AnotherExtra': 123
    }
    conn = Connection.from_dict("Test", extra_props)
    print("  ✗ BUG: from_dict accepted unknown fields without error")
    bug5_found = True
except AttributeError as e:
    print(f"  ✓ Extra fields correctly rejected: {e}")
    bug5_found = False
except Exception as e:
    print(f"  ? Different error: {e}")
    bug5_found = False

# Test 6: Resource type in output
print("\n[TEST 6] Checking resource type in output...")
conn = Connection("Test", ConnectionName="test")
output = conn.to_dict()
if 'Type' in output:
    if output['Type'] == 'AWS::CodeConnections::Connection':
        print(f"  ✓ Correct resource type: {output['Type']}")
        bug6_found = False
    else:
        print(f"  ✗ BUG: Wrong resource type: {output['Type']}")
        bug6_found = True
else:
    print("  ✗ BUG: Resource type missing from output")
    bug6_found = True

# Test 7: Tags with mixed key types
print("\n[TEST 7] Testing Tags with mixed key types...")
try:
    # Mix string and integer keys
    mixed_tags = Tags(**{"key1": "value1", 2: "value2", "key3": "value3"})
    result = mixed_tags.to_dict()
    print(f"  Mixed key types produced {len(result)} tags")
    
    # Check if all keys are preserved
    keys_found = [tag['Key'] for tag in result]
    if set(keys_found) == {"key1", 2, "key3"}:
        print("  ✓ All mixed keys preserved correctly")
        bug7_found = False
    else:
        print(f"  ? Keys found: {keys_found}")
        bug7_found = False
except Exception as e:
    print(f"  ? Error with mixed keys: {e}")
    bug7_found = False

# Summary
print("\n" + "="*60)
print("BUG HUNT SUMMARY")
print("="*60)

bugs_detected = []
if bug1_found:
    bugs_detected.append("Empty title accepted by validate_title()")
if bug2_found:
    bugs_detected.append("Whitespace-only titles accepted")
if bug3_found:
    bugs_detected.append("Invalid titles not validated in to_dict()")
if bug4_found:
    bugs_detected.append("Round-trip with None values fails")
if bug5_found:
    bugs_detected.append("from_dict accepts unknown fields")
if bug6_found:
    bugs_detected.append("Resource type issue in output")
if bug7_found:
    bugs_detected.append("Tags with mixed key types fail")

if bugs_detected:
    print(f"\n🐛 Found {len(bugs_detected)} potential bug(s):")
    for i, bug in enumerate(bugs_detected, 1):
        print(f"  {i}. {bug}")
else:
    print("\n✅ No bugs found in basic tests")

print("\nNote: These are edge cases that may or may not be considered bugs")
print("depending on the intended behavior of the library.")

# If we found the title validation bug, let's create a minimal reproduction
if bug3_found:
    print("\n" + "="*60)
    print("MINIMAL BUG REPRODUCTION")
    print("="*60)
    print("""
The following code demonstrates that Connection.to_dict() does not validate
the title format, allowing non-alphanumeric titles to pass through:

```python
from troposphere.codeconnections import Connection

# Create connection with invalid title (contains hyphens)
conn = Connection("test-conn-123", ConnectionName="myconn")

# This should fail but doesn't - title validation is not enforced
result = conn.to_dict(validation=True)
print(result)  # Outputs the CloudFormation template with invalid title

# Manual validation would catch it:
conn.validate_title()  # This raises ValueError
```

This is a bug because CloudFormation resource names must be alphanumeric,
but the validation is not automatically enforced.
""")