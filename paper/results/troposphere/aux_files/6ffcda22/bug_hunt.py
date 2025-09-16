#!/usr/bin/env python
"""Bug hunting script for troposphere.finspace"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.finspace as finspace
from troposphere import Template
import re

print("=== Bug Hunt for troposphere.finspace ===\n")

# Bug Hunt 1: Empty string as title
print("Test 1: Empty string as title")
try:
    env = finspace.Environment("", Name="TestEnv")
    print("BUG FOUND: Empty string accepted as title!")
    print(f"  Created environment with empty title: {env.title}")
except ValueError as e:
    print(f"  OK: Empty title rejected with: {e}")

# Bug Hunt 2: None as title
print("\nTest 2: None as title")
try:
    env = finspace.Environment(None, Name="TestEnv")
    if env.title is None:
        print("POTENTIAL BUG: None accepted as title")
        print(f"  Environment title is: {env.title}")
        # Try to validate
        try:
            env.to_dict()
            print("  BUG CONFIRMED: None title passes validation!")
        except Exception as e:
            print(f"  Validation fails with: {e}")
except (ValueError, TypeError) as e:
    print(f"  OK: None title rejected with: {e}")

# Bug Hunt 3: Unicode characters in title
print("\nTest 3: Unicode characters in title")
unicode_titles = ["Test🦄", "Тест", "测试", "Test\u200b"]  # emoji, cyrillic, chinese, zero-width space
for title in unicode_titles:
    try:
        env = finspace.Environment(title, Name="TestEnv")
        print(f"BUG FOUND: Unicode title '{repr(title)}' accepted!")
    except ValueError:
        print(f"  OK: Unicode title '{repr(title)}' rejected")

# Bug Hunt 4: Special characters that might break validation
print("\nTest 4: Edge case characters")
edge_cases = [
    "Test.Name",
    "Test-Name", 
    "Test_Name",
    "Test Name",
    "123",  # all numbers
    "Test\n",
    "Test\t",
    "Test\r",
]
for title in edge_cases:
    try:
        env = finspace.Environment(title, Name="TestEnv")
        valid_names = re.compile(r"^[a-zA-Z0-9]+$")
        if not valid_names.match(title):
            print(f"BUG FOUND: Invalid title '{repr(title)}' accepted!")
        else:
            print(f"  OK: Valid title '{repr(title)}' accepted")
    except ValueError:
        print(f"  OK: Invalid title '{repr(title)}' rejected")

# Bug Hunt 5: Property type validation
print("\nTest 5: Invalid property types")
try:
    # Try passing a dict instead of SuperuserParameters object
    env = finspace.Environment("Test", Name="TestEnv", 
                              SuperuserParameters={'EmailAddress': 'test@example.com'})
    print("POTENTIAL ISSUE: Raw dict accepted for SuperuserParameters")
    d = env.to_dict()
    print(f"  Result: {d.get('Properties', {}).get('SuperuserParameters')}")
except (TypeError, ValueError) as e:
    print(f"  OK: Invalid type rejected with: {e}")

# Bug Hunt 6: Missing required properties in nested objects
print("\nTest 6: Incomplete nested objects")
try:
    # Create FederationParameters without any properties
    fed = finspace.FederationParameters()
    env = finspace.Environment("Test", Name="TestEnv", FederationParameters=fed)
    d = env.to_dict()
    print("ISSUE: Empty FederationParameters accepted")
    print(f"  Result: {d.get('Properties', {}).get('FederationParameters')}")
except Exception as e:
    print(f"  Error: {e}")

# Bug Hunt 7: Extremely long strings
print("\nTest 7: Extremely long property values")
try:
    long_name = "A" * 10000
    env = finspace.Environment("Test", Name=long_name)
    d = env.to_dict()
    print(f"POTENTIAL ISSUE: Extremely long Name accepted (length: {len(d['Properties']['Name'])})")
except Exception as e:
    print(f"  Error with long name: {e}")

# Bug Hunt 8: Mutability issues
print("\nTest 8: Object mutability")
env1 = finspace.Environment("Test", Name="Original")
dict1 = env1.to_dict()
env1.Name = "Modified"  # Modify after creation
dict2 = env1.to_dict()
if dict1['Properties']['Name'] != dict2['Properties']['Name']:
    print("  OK: Properties are mutable")
    print(f"    Original: {dict1['Properties']['Name']}")
    print(f"    Modified: {dict2['Properties']['Name']}")
else:
    print("BUG: Property modification didn't work")

# Bug Hunt 9: Tags property
print("\nTest 9: Tags handling")
try:
    from troposphere import Tags
    tags = Tags({"Key1": "Value1", "Key2": "Value2"})
    env = finspace.Environment("Test", Name="TestEnv", Tags=tags)
    d = env.to_dict()
    print(f"  Tags result: {d.get('Properties', {}).get('Tags')}")
except Exception as e:
    print(f"  Error with Tags: {e}")

# Bug Hunt 10: Circular reference or deep nesting
print("\nTest 10: Deep nesting")
try:
    # Create deeply nested AttributeMapItems
    attrs = []
    for i in range(100):
        attrs.append(finspace.AttributeMapItems(Key=f"Key{i}", Value=f"Value{i}"))
    
    fed = finspace.FederationParameters(AttributeMap=attrs)
    env = finspace.Environment("Test", Name="TestEnv", FederationParameters=fed)
    d = env.to_dict()
    print(f"  OK: Handled {len(d['Properties']['FederationParameters']['AttributeMap'])} attribute items")
except Exception as e:
    print(f"  Error with deep nesting: {e}")

print("\n=== Bug Hunt Complete ===")
print("\nSummary of findings:")
print("- Check for potential issues with None titles")
print("- Check for Unicode character handling in titles")
print("- Check for extremely long string handling")
print("- Properties are mutable after object creation")