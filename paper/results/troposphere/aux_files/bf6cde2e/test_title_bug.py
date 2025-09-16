#!/usr/bin/env python3
"""Investigate title validation bug in troposphere"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.mediaconvert as mc
from troposphere import Template

print("Testing title validation bug...")

# Test 1: Empty string
print("\n1. Testing empty string as title:")
try:
    jt = mc.JobTemplate("", SettingsJson={})
    print(f"  BUG CONFIRMED: Empty string accepted as title")
    print(f"  JobTemplate.title = {jt.title!r}")
    
    # Can we serialize it?
    try:
        result = jt.to_dict()
        print(f"  Serialization succeeded: {result}")
    except Exception as e:
        print(f"  Serialization failed: {e}")
        
except ValueError as e:
    print(f"  Empty string correctly rejected: {e}")

# Test 2: String with special characters
print("\n2. Testing strings with special characters:")
test_titles = [
    "test-name",      # hyphen
    "test_name",      # underscore  
    "test.name",      # dot
    "test name",      # space
    "test@name",      # at sign
    "test/name",      # slash
    "123",            # numbers only
    "Test123",        # alphanumeric (should work)
    "тест",           # non-ASCII
    " leadingspace",  # leading space
    "trailingspace ", # trailing space
    None,             # None
]

for title in test_titles:
    try:
        jt = mc.JobTemplate(title, SettingsJson={})
        print(f"  '{title}' ACCEPTED (title={jt.title!r})")
    except (ValueError, TypeError) as e:
        error_msg = str(e)
        if "alphanumeric" in error_msg:
            print(f"  '{title}' rejected (alphanumeric check)")
        else:
            print(f"  '{title}' rejected: {error_msg}")

# Test 3: Check what the regex actually is
print("\n3. Checking the validation regex:")
import troposphere
print(f"  Regex pattern: {troposphere.valid_names.pattern}")
print(f"  Empty string matches: {bool(troposphere.valid_names.match(''))}")
print(f"  'Test123' matches: {bool(troposphere.valid_names.match('Test123'))}")
print(f"  'test-name' matches: {bool(troposphere.valid_names.match('test-name'))}")

# Test 4: Does it affect other resources?
print("\n4. Testing other resources:")
try:
    preset = mc.Preset("", SettingsJson={})
    print(f"  Preset also accepts empty title")
except ValueError:
    print(f"  Preset rejects empty title")

try:
    queue = mc.Queue("")
    print(f"  Queue also accepts empty title")
except ValueError:
    print(f"  Queue rejects empty title")

# Test 5: What about None?
print("\n5. Testing None as title:")
try:
    jt_none = mc.JobTemplate(None, SettingsJson={})
    print(f"  BUG: None accepted as title, became {jt_none.title!r}")
except (ValueError, TypeError) as e:
    print(f"  None correctly rejected: {e}")

# Test 6: Impact on CloudFormation template
print("\n6. Testing impact on CloudFormation template generation:")
template = Template()
try:
    # Try with empty string
    jt_empty = mc.JobTemplate("", template=template, SettingsJson={"test": "value"})
    cf_json = template.to_json()
    print(f"  Empty title in template: {'' in template.resources}")
    
    # Try to get the resource back
    if "" in template.resources:
        print(f"  Resource retrievable with empty key: {template.resources[''] == jt_empty}")
except Exception as e:
    print(f"  Failed to add to template: {e}")